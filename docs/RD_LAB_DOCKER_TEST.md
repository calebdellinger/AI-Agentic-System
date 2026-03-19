# RD-Lab in Docker + AutoGen smoke test

## Do you need a Gemini API key?

**No.** RD-Lab’s AutoGen path uses **`PROVIDER_MODE=LOCAL`** and talks to an **OpenAI-compatible** endpoint (vLLM).  
You only need **`GOOGLE_API_KEY`** if you later add Gemini as the lab’s LLM (not implemented in the lab loop today).

---

## What you need running

1. **An OpenAI-compatible API** (pick one):

   **A) vLLM in Docker (GPU)**  
   ```bash
   docker compose --profile llm build rd-lab-worker
   docker compose --profile llm up -d vllm-server
   ```
   Wait until vLLM is listening on port **8000**. First run may download a large model.

   **B) vLLM (or Ollama OpenAI shim) on the host**  
   In `.env` (or compose env for `rd-lab-worker`):

   - `VLLM_BASE_URL=http://host.docker.internal:8000/v1`  
   - `MODEL_NAME=<exact model id your server serves>` (must match what vLLM/Ollama exposes)

2. **RD-Lab worker**

   ```bash
   docker compose build rd-lab-worker
   docker compose up -d rd-lab-worker
   ```

   The worker is on **`net_llm`** so it can reach `vllm-server` or `host.docker.internal`.  
   It stays on **`net_lab` (internal)** for the “lab air-gap” story; **spinalcord is volumes**, not the public internet.

---

## Drop a test request

Create `research-request.json` (valid UUIDs):

```json
{
  "schema_version": "0.1.0",
  "correlation_id": "11111111-1111-1111-1111-111111111111",
  "research_question": "List three concrete patterns for schema-valid file handoffs between agent hemispheres.",
  "rationale": "Smoke-test: verify AutoGen debate and ResearchDiscovery Pydantic validation."
}
```

Copy into the shared volume:

```bash
docker cp research-request.json rd-lab-worker:/spinalcord/requests/001.json
```

---

## Check results

- **Success:** `docker exec rd-lab-worker ls /spinalcord/discoveries`  
  You should see a new `<discovery_id>.json` matching `ResearchDiscovery`.

- **Failure after 3 validation attempts:**  
  `docker exec rd-lab-worker ls /spinalcord/errors`

- **Rhythms (local audit log):**  
  `docker exec rd-lab-worker tail -20 /rhythms/lab.jsonl`

- **Consumed request:**  
  `docker exec rd-lab-worker ls /spinalcord/results/consumed_requests`

---

## Env quick reference (RD-Lab)

| Variable | Purpose |
|----------|---------|
| `PROVIDER_MODE` | Must be `LOCAL` for current lab AutoGen code path |
| `VLLM_BASE_URL` | e.g. `http://vllm-server:8000/v1` or `http://host.docker.internal:8000/v1` |
| `MODEL_NAME` | Model id passed to AutoGen (must match server) |
