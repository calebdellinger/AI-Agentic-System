from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import streamlit as st
from streamlit_autorefresh import st_autorefresh

SPINALCORD_ROOT = Path(os.getenv("SPINALCORD_ROOT", "/spinalcord"))
REQUESTS_DIR = SPINALCORD_ROOT / "requests"
DISCOVERIES_DIR = SPINALCORD_ROOT / "discoveries"
SCHEMA_VERSION = "0.1.0"


def _ensure_dirs() -> None:
    REQUESTS_DIR.mkdir(parents=True, exist_ok=True)
    DISCOVERIES_DIR.mkdir(parents=True, exist_ok=True)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_research_request(research_question: str, rationale: str) -> dict[str, Any]:
    correlation_id = uuid4()
    return {
        "request_id": str(uuid4()),
        "schema_version": SCHEMA_VERSION,
        "timestamp_utc": _utc_now_iso(),
        "correlation_id": str(correlation_id),
        "research_question": research_question.strip(),
        "rationale": rationale.strip(),
        # Future: route/throttle can read this field to pick local vs bigger models.
        # Current RD-Lab flow doesn't yet route by constraints, but we keep the
        # contract ready so the UI doesn't need to change later.
        "constraints": {},
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
        scores: list[float] = []
        for item in findings:
            if isinstance(item, dict):
                value = item.get("confidence")
                if isinstance(value, (int, float)):
                    scores.append(float(value))
        if scores:
            return sum(scores) / len(scores)

    fallback = discovery.get("confidence")
    if isinstance(fallback, (int, float)):
        return float(fallback)
    return None


def _render_findings(discovery: dict[str, Any]) -> None:
    findings = discovery.get("findings")
    if not isinstance(findings, list) or not findings:
        st.caption("No findings in this discovery yet.")
        return

    for idx, item in enumerate(findings, start=1):
        if isinstance(item, str):
            st.info(item)
            continue
        if isinstance(item, dict):
            claim = str(item.get("claim", ""))
            support = str(item.get("support_summary", ""))
            text = f"**Finding {idx}:** {claim}".strip()
            if support:
                text = f"{text}\n\n{support}"
            st.info(text)
            continue
        st.info(f"Finding {idx}: {item}")


def _render_discoveries() -> None:
    _ensure_dirs()
    files = sorted(DISCOVERIES_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        st.info("No discoveries yet. Waiting for RD-Lab output in `/spinalcord/discoveries`.")
        return

    st.subheader("Live Discoveries")
    for path in files:
        discovery = _safe_json_load(path)
        if discovery is None:
            st.warning(f"Skipped unreadable JSON file: `{path.name}`")
            continue

        left, right = st.columns([4, 1])
        with left:
            st.markdown(f"### {discovery.get('hypothesis', path.stem)}")
            st.caption(f"Discovery: {discovery.get('discovery_id', path.stem)}")
        with right:
            confidence = _extract_confidence(discovery)
            if confidence is not None:
                st.metric("Confidence", f"{confidence:.0%}")
            else:
                st.metric("Confidence", "N/A")

        _render_findings(discovery)
        with st.expander("Raw JSON (debug)"):
            st.json(discovery)


def main() -> None:
    st.set_page_config(page_title="Trinity Dashboard", page_icon=":microscope:", layout="wide")
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #0b1020;
            color: #e5e7eb;
        }
        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 0.8rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("Mad Scientist Dashboard")
    st.caption("File-based mission control via shared spinalcord volume.")

    with st.form("mission_form", clear_on_submit=False):
        research_question = st.text_area("Research Question", height=120, placeholder="What should the lab investigate?")
        rationale = st.text_input("Rationale", placeholder="Why this mission matters")
        compute_tier = st.radio(
            "Compute Tier (router policy)",
            options=["auto (router decides)", "light (local)", "heavy (big guys)"],
            horizontal=True,
            index=0,
            help="Auto lets the orchestrator choose light vs heavy to optimize cost/performance.",
        )
        deploy = st.form_submit_button("Deploy Mission", use_container_width=True, type="primary")

    if deploy:
        if not research_question.strip() or not rationale.strip():
            st.error("Both Research Question and Rationale are required.")
        else:
            payload = _build_research_request(research_question, rationale)
            if compute_tier.startswith("auto"):
                tier_value = "auto"
            elif compute_tier.startswith("light"):
                tier_value = "light"
            else:
                tier_value = "heavy"

            payload["constraints"] = {"compute_tier": tier_value}
            out_path = _write_request(payload)
            st.success(f"Mission deployed: `{out_path.name}`")
            with st.expander("Raw Request JSON (debug)"):
                st.json(payload)

    st.divider()
    st_autorefresh(interval=3000, limit=None, key="discoveries_refresh")
    _render_discoveries()


if __name__ == "__main__":
    main()
