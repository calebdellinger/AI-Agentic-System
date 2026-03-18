FROM python:3.12-slim

# Rationale: Lightweight Python runtime suitable for an air-gapped
# deployment where hemispheres rely on local volumes and internal services.
# How: Install runtime dependencies then run the orchestrator loop stub.
# Contracts:
# - Copies the monorepo into `/app` so it can import `shared_schemas`.

WORKDIR /app

COPY business-trinity/ /app/business-trinity/
COPY shared-schemas/ /app/shared-schemas/
COPY shared/ /app/shared/

RUN python -m pip install --no-cache-dir -U pip \
  && python -m pip install --no-cache-dir -r /app/business-trinity/requirements.txt

ENV PYTHONPATH="/app/business-trinity/src:/app/shared-schemas/src:/app/shared"
ENV SPINALCORD_ROOT="/spinalcord"
ENV RHYTHM_STORAGE_ROOT="/rhythms"

CMD ["python", "-m", "business_trinity.orchestrator.main_loop"]

