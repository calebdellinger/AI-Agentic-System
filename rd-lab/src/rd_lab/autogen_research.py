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
import time

from shared_schemas.config import get_provider_settings
from shared_schemas.research_discovery import ResearchDiscovery

from rd_lab.bridge.outbox import write_research_discovery
from rd_lab.models.research_request import ResearchRequest
from rd_lab.storage.log_writer import append_rhythm_event


MAX_VALIDATION_ATTEMPTS = 3

# Debug mode runtime evidence.
#
# Rationale: When schema validation fails, we need to know what the model
# actually returned (JSON shape + field types) so fixes are grounded in
# evidence.
# How: Append NDJSON lines to the workspace log path (mounted into the
# container at `/workspace`).
DEBUG_SESSION_ID = "ee17f7"
DEBUG_RUN_ID = os.getenv("DEBUG_RUN_ID", "pre-fix")
DEBUG_LOG_PATH = os.getenv("DEBUG_LOG_PATH", "/workspace/debug-ee17f7.log")


def _append_debug_log(*, hypothesis_id: str, location: str, message: str, data: dict[str, Any]) -> None:
    """
    Rationale: Provide runtime evidence without leaking secrets.

    How:
    - Writes one NDJSON line to `debug-ee17f7.log` (workspace-mounted).

    Contracts:
    - Must not include secrets/tokens/keys.
    - Should keep `data` small (truncate large strings upstream).
    """

    payload = {
        "sessionId": DEBUG_SESSION_ID,
        "runId": DEBUG_RUN_ID,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    try:
        Path(DEBUG_LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, sort_keys=True, ensure_ascii=False) + "\n")
    except Exception:
        # Rationale: Debug logging must never crash the worker.
        pass


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

    # Rationale: naive "first { .. last }" extraction fails when the model
    # emits multiple JSON objects or trailing non-JSON text.
    # How: Extract the first *balanced* top-level JSON object by tracking
    # brace depth while respecting quoted strings.
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object detected in model output")

    depth = 0
    in_string = False
    escape = False

    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]

    raise ValueError("No balanced JSON object detected in model output")


def _parse_discovery_from_autogen_text(text: str) -> ResearchDiscovery:
    """
    Rationale: Convert AutoGen output text into validated schema.

    How:
    - Extract JSON from the text.
    - Validate with `ResearchDiscovery`.
    """

    raise NotImplementedError


def _coerce_confidence(value: Any) -> float:
    """
    Rationale: Pydantic requires `confidence` in [0,1]. LLM outputs may
    provide strings/nulls; we coerce safely.
    """

    try:
        f = float(value)
    except Exception:
        return 0.5
    if f < 0.0:
        return 0.0
    if f > 1.0:
        return 1.0
    return f


def _normalize_candidate_json(
    *,
    candidate: dict[str, Any],
    request: ResearchRequest,
) -> dict[str, Any]:
    """
    Rationale: If the model emits JSON in an adjacent-but-wrong shape
    (observed at runtime), normalize it deterministically so the final output
    validates against the shared schema while preserving Decision DNA fields.

    How:
    - Always fill required schema fields from the request when missing.
    - If the model returns a `research_question` object resembling a `Finding`,
      treat it as the first `finding`.
    """

    # --- Correlation ---
    correlation_id = request.correlation_id

    # --- Rationale ("why") ---
    rationale = candidate.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        rationale = request.rationale

    # --- Hypothesis ---
    hypothesis = candidate.get("hypothesis")
    if not isinstance(hypothesis, str) or not hypothesis.strip():
        # Observed failure mode: model emits `research_question: {claim, ...}`
        rq = candidate.get("research_question")
        if isinstance(rq, dict):
            claim = rq.get("claim")
            if isinstance(claim, str) and claim.strip():
                hypothesis = claim
            else:
                hypothesis = request.research_question
        else:
            hypothesis = request.research_question

    # --- Methods ---
    methods = candidate.get("methods")
    if isinstance(methods, list):
        methods_out: list[dict[str, Any]] = []
        for m in methods:
            if isinstance(m, dict):
                methods_out.append(m)
        methods = methods_out
    else:
        methods = []

    # --- Findings ---
    findings = candidate.get("findings")
    if not isinstance(findings, list):
        # Observed failure mode: model uses `research_question` as a Finding.
        rq = candidate.get("research_question")
        if isinstance(rq, dict):
            findings = [rq]
        else:
            findings = []

    findings_out: list[dict[str, Any]] = []
    for f in findings:
        if not isinstance(f, dict):
            continue
        claim = f.get("claim")
        if not isinstance(claim, str) or not claim.strip():
            claim = request.research_question
        support_summary = f.get("support_summary")
        if not isinstance(support_summary, str) or not support_summary.strip():
            support_summary = request.research_question
        confidence = _coerce_confidence(f.get("confidence"))
        findings_out.append(
            {
                "claim": claim,
                "support_summary": support_summary,
                "confidence": confidence,
            }
        )

    # --- Next questions ---
    next_questions = candidate.get("next_questions")
    if isinstance(next_questions, list):
        nq_out: list[str] = []
        for q in next_questions:
            if isinstance(q, str):
                nq_out.append(q)
            else:
                nq_out.append(str(q))
        next_questions = nq_out
    else:
        next_questions = []

    # --- Artifact refs ---
    artifact_refs = candidate.get("artifact_refs")
    artifact_out: list[dict[str, str]] = []
    if isinstance(artifact_refs, list):
        for a in artifact_refs:
            if isinstance(a, dict):
                artifact_out.append(
                    {str(k): str(v) for k, v in a.items() if k is not None and v is not None}
                )

    return {
        "schema_version": "0.1.0",
        "correlation_id": correlation_id,
        "hypothesis": hypothesis,
        "methods": methods,
        "findings": findings_out,
        "next_questions": next_questions,
        "rationale": rationale,
        "linked_decision_record_id": None,
        "artifact_refs": artifact_out,
    }


def _parse_discovery_from_autogen_text(text: str, *, request: ResearchRequest) -> ResearchDiscovery:
    """
    Rationale: Parse and validate model output into `ResearchDiscovery`.

    How:
    - Extract first JSON object (balanced braces).
    - Deserialize to dict.
    - Normalize into schema-required shape.
    - Validate with shared Pydantic schema.
    """

    raw_json = _extract_first_json_object(text)

    #region debug_log_H2_json_extraction
    _append_debug_log(
        hypothesis_id="H2_json_extraction",
        location="_parse_discovery_from_autogen_text:raw_json",
        message="Extracted JSON substring for parsing.",
        data={
            "extracted_len": len(raw_json),
            "extracted_prefix": raw_json[:200],
        },
    )
    #endregion

    candidate = json.loads(raw_json)
    if not isinstance(candidate, dict):
        raise ValueError("Extracted JSON was not an object")

    #region debug_log_H5_normalization_input
    _append_debug_log(
        hypothesis_id="H5_normalization_input",
        location="_parse_discovery_from_autogen_text:normalization_input_prefix",
        message="Normalizing candidate JSON into schema-required shape.",
        data={"candidate_prefix": raw_json[:200]},
    )
    #endregion

    normalized = _normalize_candidate_json(candidate=candidate, request=request)

    #region debug_log_H5_normalization_output
    _append_debug_log(
        hypothesis_id="H5_normalization_output",
        location="_parse_discovery_from_autogen_text:normalization_output_keys",
        message="Normalization produced schema-required keys.",
        data={"keys": sorted(list(normalized.keys()))},
    )
    #endregion

    return ResearchDiscovery.model_validate(normalized)


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
            "Your task is to output a SINGLE JSON object that validates "
            "against the shared_schemas.ResearchDiscovery schema. "
            "Output JSON ONLY (no markdown, no commentary). "
            "Use EXACT field names and EXACT types."
        ),
        llm_config=llm_config,
        code_execution_config=False,
    )

    critic = AssistantAgent(
        name="critic",
        system_message=(
            "You are the Constitution critic. "
            "You validate and correct JSON so it matches the "
            "shared_schemas.ResearchDiscovery schema exactly. "
            "Output JSON ONLY."
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

    # Rationale: Provide an explicit schema-shaped template to reduce
    # hallucinated key names and wrong nested types.
    schema_template = {
        "discovery_id": "UUID-string",
        "schema_version": "0.1.0",
        "timestamp_utc": "ISO-8601-string",
        "correlation_id": discovery_prompt["correlation_id"],
        "hypothesis": "string",
        "methods": [],
        "findings": [
            {
                "claim": "string",
                "support_summary": "string",
                "confidence": 0.75,
            }
        ],
        "next_questions": ["string"],
        "rationale": "string (non-empty)",
        "linked_decision_record_id": None,
        # artifact_refs is a list[dict[str,str]]. For scaffolding we allow empty.
        "artifact_refs": [],
    }

    # Step 1: researcher attempts schema-shaped JSON.
    researcher_chat = user_proxy.initiate_chat(
        researcher,
        message=(
            "Produce a ResearchDiscovery JSON object that matches this exact schema template. "
            "Replace placeholder values with your own content based on the request. "
            "Strict rules: "
            "1) findings must be a list of objects with keys claim/support_summary/confidence (confidence is a number 0..1). "
            "2) next_questions must be a list of strings (NOT objects). "
            "3) schema_version must be exactly \"0.1.0\". "
            "4) correlation_id must equal the request correlation_id. "
            "5) artifact_refs must be a list of dict[str,str] (use [] if unsure).\n\n"
            f"Request JSON: {json.dumps(discovery_prompt, ensure_ascii=False)}\n\n"
            f"Schema Template: {json.dumps(schema_template, ensure_ascii=False)}\n\n"
            "Return JSON ONLY."
        ),
        max_turns=2,
        silent=True,
    )
    researcher_text = _extract_chat_last_content(researcher_chat)

    # Step 2: critic corrects and outputs JSON-only.
    critic_chat = user_proxy.initiate_chat(
        critic,
        message=(
            "Here is the candidate JSON (may be invalid). "
            "Validate and correct it so it matches ResearchDiscovery schema EXACTLY. "
            "Strictly enforce: findings as list of {claim,support_summary,confidence}; "
            "next_questions as list[str]. Return JSON ONLY.\n\n"
            f"Candidate:\n{researcher_text}\n"
        ),
        max_turns=2,
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

    #region debug_log_H1_model_usage
    provider_settings = get_provider_settings()
    _append_debug_log(
        hypothesis_id="H1_model_usage",
        location="run_autogen_with_pydantic_retries:init",
        message="Starting AutoGen debate run with provider settings.",
        data={
            "provider_mode": provider_settings.provider_mode,
            "fallback_provider_mode": provider_settings.fallback_provider_mode,
            "vllm_base_url": provider_settings.vllm_base_url,
            "model_name": provider_settings.model_name,
            "max_validation_attempts": MAX_VALIDATION_ATTEMPTS,
        },
    )
    #endregion

    last_error: Optional[dict[str, Any]] = None
    for attempt in range(1, MAX_VALIDATION_ATTEMPTS + 1):
        candidate_text = _run_autogen_research_json(request)

        #region debug_log_H4_chat_output
        _append_debug_log(
            hypothesis_id="H4_chat_output",
            location="run_autogen_with_pydantic_retries:critic_output",
            message="Captured AutoGen critic output prior to parsing.",
            data={
                "attempt": attempt,
                "output_prefix": candidate_text[:250],
                "has_left_brace": "{" in candidate_text,
                "has_right_brace": "}" in candidate_text,
            },
        )
        #endregion
        try:
            discovery = _parse_discovery_from_autogen_text(candidate_text, request=request)
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

            #region debug_log_H3_schema_mismatch
            err_data: dict[str, Any] = {
                "attempt": attempt,
                "error_type": type(e).__name__,
                "error_message_prefix": str(e)[:250],
            }
            try:
                # Pydantic v2 exposes `errors()` for ValidationError.
                if hasattr(e, "errors"):
                    err_data["pydantic_errors"] = [d.get("loc", None) for d in e.errors()]  # type: ignore[attr-defined]
            except Exception:
                pass
            _append_debug_log(
                hypothesis_id="H3_schema_mismatch",
                location="run_autogen_with_pydantic_retries:validation_failure",
                message="AutoGen output failed validation/parsing.",
                data=err_data,
            )
            #endregion
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

