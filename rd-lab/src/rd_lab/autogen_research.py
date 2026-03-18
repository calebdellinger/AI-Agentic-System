"""
Rationale: Encapsulate the AutoGen debate loop for generating
`ResearchDiscovery` artifacts.

How (Phase 2 - AutoGen only):
- Consumes a validated `ResearchRequest`.
- Runs a local-only AutoGen debate to produce a JSON payload.
- Parses the payload and validates it using shared Pydantic schemas.
- Retries validation up to 3 times before signaling an error artifact.

Contracts:
- Never execute external tools during debate (no code execution).
- Must log:
  - `#DECISION_RATIONALE_WRITTEN` before debate starts (using request rationale)
  - `#SYSTEM_VALIDATION_FAILURE` per failed validation attempt
- On success, writes `ResearchDiscovery` via outbox.
- On repeated validation failure, writes an error artifact and stops (no
  escalation from Lab; orchestrator may escalate later).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Optional
from pathlib import Path

from shared_schemas.config import get_provider_settings
from shared_schemas.research_discovery import ResearchDiscovery

from rd_lab.bridge.outbox import write_research_discovery
from rd_lab.models.research_request import ResearchRequest
from rd_lab.storage.log_writer import append_rhythm_event


MAX_VALIDATION_ATTEMPTS = 3


def _extract_first_json_object(text: str) -> str:
    """
    Rationale: LLMs often wrap JSON in text; extract the JSON object.

    How:
    - Find the first `{` and the last `}` and slice between them.

    Contracts:
    - Returns a string that should be parseable by `json.loads`.
    - If extraction fails, raises `ValueError`.
    """

    if not isinstance(text, str):
        raise ValueError("LLM output was not a string")

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object detected in model output")
    return text[start : end + 1]


def _parse_discovery_from_autogen_text(text: str) -> ResearchDiscovery:
    """
    Rationale: Convert AutoGen output text into validated schema.

    How:
    - Extract JSON from the text.
    - Validate with `ResearchDiscovery`.
    """

    raw_json = _extract_first_json_object(text)
    data = json.loads(raw_json)
    return ResearchDiscovery.model_validate(data)


def _build_llm_config_for_autogen():
    """
    Rationale: Bridge shared provider config into AutoGen's LLM config.

    How:
    - Uses vLLM via OpenAI-compatible base URL when `PROVIDER_MODE=LOCAL`.

    Contracts:
    - Supports scaffolding for LOCAL mode.
  """

    settings = get_provider_settings()
    if settings.provider_mode != "LOCAL":
        raise ValueError(
            f"rd-lab scaffolding currently assumes LOCAL provider mode; got {settings.provider_mode}"
        )

    model = settings.model_name or "local-model"
    # Rationale: AutoGen's ConversableAgent expects OpenAI-compatible config_list.
    return {
        "config_list": [
            {
                "model": model,
                "base_url": settings.vllm_base_url,
                "api_key": "local",
            }
        ],
        "temperature": float(os.getenv("AUTOGEN_TEMPERATURE", "0.2")),
    }


def _extract_chat_last_content(chat_result: Any) -> str:
    """
    Rationale: AutoGen return types can vary; robustly extract final text.

    How:
    - Try common attributes: `chat_history`, `summary`, `final`.
    """

    for attr in ("summary", "final", "result"):
        val = getattr(chat_result, attr, None)
        if isinstance(val, str) and val.strip():
            return val

    history = getattr(chat_result, "chat_history", None)
    if isinstance(history, list) and history:
        last = history[-1]
        if isinstance(last, dict):
            content = last.get("content")
            if isinstance(content, str) and content.strip():
                return content
        if isinstance(last, str) and last.strip():
            return last

    # Best-effort fallback.
    text = str(chat_result)
    if text.strip():
        return text
    raise ValueError("Unable to extract model output from AutoGen result")


def _run_autogen_research_json(request: ResearchRequest) -> str:
    """
    Rationale: AutoGen debate loop should return candidate discovery JSON.

    How:
    - Uses two AutoGen agents (researcher + critic) to improve adherence
      to the schema.
    - The critic is instructed to output a corrected JSON object.

    Contracts:
    - Both agents are configured with `code_execution_config=False` so the
      debate is not allowed to run code.
    - Output must be JSON-only (critic enforces correction).
    """

    # Local import so scaffolding doesn't break if autogen changes.
    from autogen import AssistantAgent, UserProxyAgent

    llm_config = _build_llm_config_for_autogen()

    researcher = AssistantAgent(
        name="researcher",
        system_message=(
            "You are the Mad Scientist researcher. "
            "Generate a single ResearchDiscovery JSON object that is strictly valid. "
            "Output JSON only, with required fields including `rationale`."
        ),
        llm_config=llm_config,
        code_execution_config=False,
    )

    critic = AssistantAgent(
        name="critic",
        system_message=(
            "You are the Constitution critic. "
            "Validate the provided JSON against ResearchDiscovery requirements. "
            "If invalid, output a corrected JSON-only object. "
            "Always ensure `rationale` is present and non-empty."
        ),
        llm_config=llm_config,
        code_execution_config=False,
    )

    user_proxy = UserProxyAgent(
        name="user_proxy",
        human_input_mode="NEVER",
        code_execution_config=False,
    )

    discovery_prompt = {
        "research_question": request.research_question,
        "constraints": request.constraints,
        "correlation_id": str(request.correlation_id),
        "linked_decision_record_id": str(request.linked_decision_record_id)
        if request.linked_decision_record_id
        else None,
    }

    # Step 1: researcher attempts schema-shaped JSON.
    researcher_chat = user_proxy.initiate_chat(
        researcher,
        message=(
            "Produce a ResearchDiscovery JSON object with fields: "
            "`discovery_id` (UUID), `schema_version` (0.1.0), "
            "`timestamp_utc`, `correlation_id`, `hypothesis`, `methods`, `findings`, "
            "`next_questions`, `rationale`, `linked_decision_record_id`, `artifact_refs`.\n"
            f"Request JSON: {json.dumps(discovery_prompt, ensure_ascii=False)}\n"
            "JSON ONLY. Do not wrap in markdown."
        ),
        max_turns=1,
        silent=True,
    )
    researcher_text = _extract_chat_last_content(researcher_chat)

    # Step 2: critic corrects and outputs JSON-only.
    critic_chat = user_proxy.initiate_chat(
        critic,
        message=(
            "Here is the candidate JSON (may be invalid). "
            "Return corrected ResearchDiscovery JSON ONLY.\n\n"
            f"Candidate:\n{researcher_text}\n"
            "JSON ONLY. Do not wrap in markdown."
        ),
        max_turns=1,
        silent=True,
    )
    critic_text = _extract_chat_last_content(critic_chat)
    return critic_text


@dataclass(frozen=True)
class DiscoveryRunOutcome:
    success: bool
    discovery: Optional[ResearchDiscovery] = None
    last_error: Optional[dict[str, Any]] = None


def run_autogen_with_pydantic_retries(
    *,
    request: ResearchRequest,
    spinalcord_root: str,
    rhythms_root: str,
) -> DiscoveryRunOutcome:
    """
    Rationale: Validation failure must be observable and deterministic.

    How:
    - Attempt AutoGen -> parse -> validate up to MAX_VALIDATION_ATTEMPTS.
    - Log a rhythm event for each validation failure.
    - If still failing, return outcome with an error summary for error artifact.
    """

    # Log rationale before any LLM debate (your Decision DNA rule).
    append_rhythm_event(
        rhythms_root=rhythms_root,
        hemisphere="lab",
        event_type="#DECISION_RATIONALE_WRITTEN",
        payload={
            "msg": "Starting AutoGen research debate",
            "correlation_id": str(request.correlation_id),
            "request_id": str(request.request_id),
            "rationale": request.rationale,
        },
        correlation_id=request.correlation_id,
        record_id=request.linked_decision_record_id,
    )

    last_error: Optional[dict[str, Any]] = None
    for attempt in range(1, MAX_VALIDATION_ATTEMPTS + 1):
        candidate_text = _run_autogen_research_json(request)
        try:
            discovery = _parse_discovery_from_autogen_text(candidate_text)
            # Enforce correlation id consistency (Defense-in-depth).
            if discovery.correlation_id != request.correlation_id:
                raise ValueError(
                    f"correlation_id mismatch: discovery={discovery.correlation_id}, request={request.correlation_id}"
                )
            # Write to spinalcord.
            write_research_discovery(spinalcord_root, discovery)
            return DiscoveryRunOutcome(success=True, discovery=discovery)
        except Exception as e:  # noqa: BLE001
            last_error = {
                "attempt": attempt,
                "error_type": type(e).__name__,
                "error_message": str(e),
            }
            append_rhythm_event(
                rhythms_root=rhythms_root,
                hemisphere="lab",
                event_type="#SYSTEM_VALIDATION_FAILURE",
                payload={
                    "msg": "ResearchDiscovery validation failed (AutoGen output).",
                    "attempt": attempt,
                    "request_id": str(request.request_id),
                    "correlation_id": str(request.correlation_id),
                    "last_error": last_error,
                },
                correlation_id=request.correlation_id,
            )

    return DiscoveryRunOutcome(success=False, last_error=last_error)


def write_validation_error_artifact(
    *,
    spinalcord_root: str,
    request: ResearchRequest,
    outcome: DiscoveryRunOutcome,
) -> Optional[str]:
    """
    Rationale: Orchestrator needs a tangible signal when validation fails.

    How:
    - Writes an error JSON artifact in `spinalcord/errors/`.
    """

    if outcome.success:
        return None

    errors_dir = Path(spinalcord_root) / "errors"
    errors_dir.mkdir(parents=True, exist_ok=True)
    p = errors_dir / f"{request.request_id}-validation-failed.json"
    payload = {
        "request_id": str(request.request_id),
        "correlation_id": str(request.correlation_id),
        "schema_version": str(request.schema_version),
        "error": outcome.last_error,
        "message": "Local AutoGen produced invalid ResearchDiscovery after retries. Orchestrator may escalate.",
    }
    p.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return str(p)

