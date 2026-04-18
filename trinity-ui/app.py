from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import streamlit as st
from streamlit_autorefresh import st_autorefresh

SPINALCORD_ROOT = Path(os.getenv("SPINALCORD_ROOT", "/spinalcord"))
REQUESTS_DIR = SPINALCORD_ROOT / "requests"
DISCOVERIES_DIR = SPINALCORD_ROOT / "discoveries"
DEBATES_DIR = SPINALCORD_ROOT / "debates"
SCHEMA_VERSION = "0.1.0"
MAX_CONTEXT_CHARS = 6000
SUMMARY_LINE_MAX_CHARS = 220


def _ensure_dirs() -> None:
    REQUESTS_DIR.mkdir(parents=True, exist_ok=True)
    DISCOVERIES_DIR.mkdir(parents=True, exist_ok=True)
    DEBATES_DIR.mkdir(parents=True, exist_ok=True)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tier_value(label: str) -> str:
    if label.startswith("auto"):
        return "auto"
    if label.startswith("light"):
        return "light"
    if label.startswith("cloud"):
        return "cloud"
    return "heavy"


def _build_research_request(*, research_text: str, rationale: str, constraints: dict[str, Any]) -> dict[str, Any]:
    correlation_id = uuid4()
    return {
        "request_id": str(uuid4()),
        "schema_version": SCHEMA_VERSION,
        "timestamp_utc": _utc_now_iso(),
        "correlation_id": str(correlation_id),
        "research_question": research_text.strip(),
        "rationale": rationale.strip(),
        "constraints": constraints,
        "linked_decision_record_id": None,
    }


def _write_request(payload: dict[str, Any]) -> Path:
    _ensure_dirs()
    request_id = payload["request_id"]
    out_path = REQUESTS_DIR / f"{request_id}.json"
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return out_path


def _safe_json_load(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _extract_confidence(discovery: dict[str, Any]) -> float | None:
    findings = discovery.get("findings")
    if isinstance(findings, list):
        values: list[float] = []
        for item in findings:
            if isinstance(item, dict):
                score = item.get("confidence")
                if isinstance(score, (float, int)):
                    values.append(float(score))
        if values:
            return sum(values) / len(values)
    return None


def _discovery_to_markdown(discovery: dict[str, Any]) -> str:
    hypothesis = str(discovery.get("hypothesis", "")).strip()
    rationale = str(discovery.get("rationale", "")).strip()
    next_questions = discovery.get("next_questions")
    findings = discovery.get("findings")
    confidence = _extract_confidence(discovery)

    lines: list[str] = []
    if hypothesis:
        lines.append(f"**Hypothesis**: {hypothesis}")
    if confidence is not None:
        lines.append(f"**Confidence**: {confidence:.0%}")

    if isinstance(findings, list) and findings:
        lines.append("**Key findings**:")
        for idx, item in enumerate(findings[:6], start=1):
            if isinstance(item, dict):
                claim = str(item.get("claim", "")).strip()
                support = str(item.get("support_summary", "")).strip()
                if support:
                    lines.append(f"{idx}. {claim} - {support}")
                else:
                    lines.append(f"{idx}. {claim}")
            else:
                lines.append(f"{idx}. {item}")

    if rationale:
        lines.append(f"**Rationale**: {rationale}")

    if isinstance(next_questions, list) and next_questions:
        joined = "; ".join(str(x) for x in next_questions[:3])
        lines.append(f"**Next questions**: {joined}")

    if not lines:
        return "No structured output was returned in this discovery yet."
    return "\n\n".join(lines)


def _init_state() -> None:
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "pending_requests" not in st.session_state:
        st.session_state.pending_requests = {}
    if "processed_discoveries" not in st.session_state:
        st.session_state.processed_discoveries = set()


def _append_message(role: str, content: str, **meta: Any) -> None:
    st.session_state.chat_messages.append(
        {
            "role": role,
            "content": content,
            "created_utc": _utc_now_iso(),
            **meta,
        }
    )


def _strip_markdown_for_memory(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*_#>-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _compact_text_for_memory(text: str, *, max_chars: int = SUMMARY_LINE_MAX_CHARS) -> str:
    cleaned = _strip_markdown_for_memory(text)
    if len(cleaned) <= max_chars:
        return cleaned

    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", cleaned) if p.strip()]
    if parts:
        out = parts[0]
        if len(out) > max_chars:
            out = out[:max_chars].rstrip()
        if not out.endswith((".", "!", "?")):
            out += "."
        return out

    out = cleaned[:max_chars].rstrip()
    if not out.endswith((".", "!", "?")):
        out += "."
    return out


def _format_context_block(*, include_turns: int, strategy: str, max_chars: int) -> str:
    """
    Build a compact rolling transcript for follow-up questions.

    Rationale:
    - The RD-Lab request schema accepts one `research_question` string.
    - We embed recent turns in that field so follow-ups preserve context.
    """

    if include_turns <= 0:
        return ""

    relevant: list[dict[str, Any]] = []
    for msg in st.session_state.chat_messages:
        if msg.get("pending"):
            continue
        role = msg.get("role")
        content = str(msg.get("content", "")).strip()
        if role not in {"user", "assistant"} or not content:
            continue
        relevant.append({"role": role, "content": content})

    if not relevant:
        return ""

    recent = relevant[-include_turns:]
    lines = ["Conversation context:"]
    for msg in recent:
        role_name = "User" if msg["role"] == "user" else "Assistant"
        content = msg["content"]
        if strategy == "summarized":
            content = _compact_text_for_memory(content)
        lines.append(f"{role_name}: {content}")

    context = "\n".join(lines).strip()
    if len(context) > max_chars:
        context = context[-max_chars:]
    return context


def _compose_research_text(
    *,
    user_prompt: str,
    include_memory: bool,
    memory_turns: int,
    memory_strategy: str,
    memory_max_chars: int,
) -> str:
    if not include_memory:
        return user_prompt.strip()

    context = _format_context_block(
        include_turns=memory_turns,
        strategy=memory_strategy,
        max_chars=memory_max_chars,
    )
    if not context:
        return user_prompt.strip()

    return (
        f"{context}\n\n"
        "Current user question:\n"
        f"{user_prompt.strip()}\n\n"
        "Answer the current question directly while using the conversation context when relevant."
    )


def _replace_pending_reply(correlation_id: str, content: str, discovery: dict[str, Any]) -> bool:
    for idx, msg in enumerate(st.session_state.chat_messages):
        if msg.get("role") != "assistant":
            continue
        if msg.get("correlation_id") != correlation_id:
            continue
        if not msg.get("pending"):
            continue
        st.session_state.chat_messages[idx] = {
            **msg,
            "pending": False,
            "content": content,
            "discovery_id": str(discovery.get("discovery_id", "")),
        }
        return True
    return False


def _sync_discoveries_into_chat() -> None:
    _ensure_dirs()
    files = sorted(DISCOVERIES_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime)
    for path in files:
        discovery = _safe_json_load(path)
        if discovery is None:
            continue

        discovery_id = str(discovery.get("discovery_id", path.stem))
        if discovery_id in st.session_state.processed_discoveries:
            continue

        correlation_id = str(discovery.get("correlation_id", ""))
        if not correlation_id:
            st.session_state.processed_discoveries.add(discovery_id)
            continue

        if correlation_id not in st.session_state.pending_requests:
            # Keep chat scoped to this session's submitted prompts.
            continue

        response_md = _discovery_to_markdown(discovery)
        replaced = _replace_pending_reply(correlation_id, response_md, discovery)
        if not replaced:
            _append_message(
                "assistant",
                response_md,
                correlation_id=correlation_id,
                pending=False,
                discovery_id=discovery_id,
            )

        st.session_state.pending_requests.pop(correlation_id, None)
        st.session_state.processed_discoveries.add(discovery_id)


def _render_live_debate_panel() -> None:
    files = sorted(DEBATES_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    with st.expander("Live agent debate (debug)", expanded=False):
        if not files:
            st.caption("Debate transcript appears here while RD-Lab is processing.")
            return

        latest = files[0]
        st.caption(f"Latest transcript: `{latest.name}`")
        try:
            raw_lines = latest.read_text(encoding="utf-8").splitlines()
        except OSError:
            st.warning("Could not read debate transcript.")
            return

        for line in raw_lines:
            line = line.strip()
            if not line:
                continue
            try:
                obj: dict[str, Any] = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("type") == "turn":
                agent = str(obj.get("agent", "agent"))
                content = str(obj.get("content", ""))
                st.markdown(f"**{agent}**")
                st.write(content)


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at 10% 10%, #1d2847 0%, rgba(29, 40, 71, 0) 35%),
                radial-gradient(circle at 90% 20%, #2d1f4f 0%, rgba(45, 31, 79, 0) 32%),
                linear-gradient(160deg, #0b1020 0%, #0f172e 60%, #0a0f1c 100%);
            color: #e8ecf8;
        }
        .block-container {
            max-width: 920px;
            padding-top: 1.2rem;
            padding-bottom: 6rem;
        }
        [data-testid="stChatMessage"] {
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.12);
            background: linear-gradient(
                145deg,
                rgba(255, 255, 255, 0.08) 0%,
                rgba(255, 255, 255, 0.03) 100%
            );
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.08),
                0 12px 24px rgba(0, 0, 0, 0.25);
            margin-bottom: 0.85rem;
            padding: 0.4rem 0.2rem;
            backdrop-filter: blur(8px);
        }
        [data-testid="stChatInput"] {
            border-radius: 14px;
            border: 1px solid rgba(255, 255, 255, 0.18);
            background: rgba(9, 15, 30, 0.78);
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.06),
                0 10px 18px rgba(0, 0, 0, 0.35);
        }
        div[data-testid="stStatusWidget"] {
            border-radius: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _submit_prompt(
    user_prompt: str,
    rationale: str,
    compute_tier_label: str,
    include_memory: bool,
    memory_turns: int,
    memory_strategy: str,
    memory_max_chars: int,
    use_company_knowledge: bool,
    knowledge_top_k: int,
    knowledge_max_chars: int,
) -> None:
    tier = _tier_value(compute_tier_label)
    research_text = _compose_research_text(
        user_prompt=user_prompt,
        include_memory=include_memory,
        memory_turns=memory_turns,
        memory_strategy=memory_strategy,
        memory_max_chars=memory_max_chars,
    )
    constraints: dict[str, Any] = {"compute_tier": tier}
    if include_memory:
        constraints["chat_memory_turns"] = int(memory_turns)
        constraints["chat_memory_strategy"] = memory_strategy
        constraints["chat_memory_max_chars"] = int(memory_max_chars)
    constraints["use_company_knowledge"] = bool(use_company_knowledge)
    if use_company_knowledge:
        constraints["knowledge_top_k"] = int(knowledge_top_k)
        constraints["knowledge_max_chars"] = int(knowledge_max_chars)

    payload = _build_research_request(
        research_text=research_text,
        rationale=rationale,
        constraints=constraints,
    )
    out_path = _write_request(payload)
    correlation_id = str(payload["correlation_id"])

    _append_message(
        "user",
        user_prompt.strip(),
        correlation_id=correlation_id,
        request_id=payload["request_id"],
        request_file=out_path.name,
        memory_enabled=include_memory,
    )
    _append_message(
        "assistant",
        "Processing your prompt with RD-Lab. Response will appear here in this thread.",
        correlation_id=correlation_id,
        pending=True,
    )
    st.session_state.pending_requests[correlation_id] = {
        "request_id": payload["request_id"],
        "request_file": out_path.name,
    }


def main() -> None:
    st.set_page_config(page_title="Trinity Chat", page_icon=":speech_balloon:", layout="wide")
    _inject_styles()
    _init_state()
    _ensure_dirs()

    st_autorefresh(interval=3000, limit=None, key="chat_refresh")
    _sync_discoveries_into_chat()

    st.title("Trinity Chat Console")
    st.caption("Prompt RD-Lab from here and receive responses in this same chat thread.")

    with st.sidebar:
        st.subheader("Session Controls")
        rationale = st.text_area(
            "Default rationale",
            value="User requested this mission from Trinity chat UI.",
            help="Attached to each request for auditability.",
            height=100,
        )
        compute_tier = st.radio(
            "Compute tier",
            options=[
                "auto (router decides)",
                "light (local)",
                "heavy (local big)",
                "cloud (provider escalation)",
            ],
            index=0,
        )
        include_memory = st.toggle(
            "Conversation memory",
            value=True,
            help="Include recent turns in each new request so follow-up questions keep context.",
        )
        memory_turns = st.slider(
            "Memory window (messages)",
            min_value=2,
            max_value=16,
            value=8,
            step=2,
            disabled=not include_memory,
        )
        memory_strategy = st.selectbox(
            "Memory strategy",
            options=["summarized", "raw"],
            index=0,
            disabled=not include_memory,
            help=(
                "Summarized is cheaper: each previous turn is compacted before being sent as context. "
                "Raw sends full turn text."
            ),
        )
        memory_max_chars = st.slider(
            "Memory context budget (chars)",
            min_value=800,
            max_value=MAX_CONTEXT_CHARS,
            value=1800,
            step=200,
            disabled=not include_memory,
            help="Hard cap for total injected memory context each request.",
        )
        use_company_knowledge = st.toggle(
            "Use company knowledge retrieval",
            value=False,
            help="Inject top matching snippets from company knowledge docs into the request context.",
        )
        knowledge_top_k = st.slider(
            "Knowledge snippets (top_k)",
            min_value=1,
            max_value=8,
            value=3,
            step=1,
            disabled=not use_company_knowledge,
        )
        knowledge_max_chars = st.slider(
            "Knowledge context budget (chars)",
            min_value=600,
            max_value=5000,
            value=1800,
            step=200,
            disabled=not use_company_knowledge,
        )
        if st.button("Clear chat history", use_container_width=True):
            st.session_state.chat_messages = []
            st.session_state.pending_requests = {}
            st.session_state.processed_discoveries = set()
            st.rerun()

        pending = len(st.session_state.pending_requests)
        st.caption(f"Pending responses: {pending}")
        _render_live_debate_panel()

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg.get("role", "assistant")):
            st.markdown(msg.get("content", ""))
            if msg.get("pending"):
                st.caption("Working...")

    prompt = st.chat_input("Ask a research question...")
    if prompt:
        if not prompt.strip():
            st.warning("Please enter a non-empty prompt.")
        elif not rationale.strip():
            st.warning("Please provide a rationale in the sidebar.")
        else:
            _submit_prompt(
                prompt,
                rationale,
                compute_tier,
                include_memory,
                memory_turns,
                memory_strategy,
                memory_max_chars,
                use_company_knowledge,
                knowledge_top_k,
                knowledge_max_chars,
            )
            st.rerun()


if __name__ == "__main__":
    main()
