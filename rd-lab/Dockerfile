FROM python:3.12-slim

# Rationale: Lab must operate without outbound internet access and must
# treat the shared volume as the only bridge.
# How: Installs dependencies then runs the lab worker loop stub.
#
# Contracts:
# - Copies monorepo into `/app` so it can import `shared_schemas`.
# - Uses runtime env vars to locate the spinalcord and local rhythms.

WORKDIR /app

COPY rd-lab/ /app/rd-lab/
COPY shared-schemas/ /app/shared-schemas/
COPY shared/ /app/shared/

RUN python -m pip install --no-cache-dir -U pip \
  && python -m pip install --no-cache-dir -r /app/rd-lab/requirements.txt

ENV PYTHONPATH="/app/rd-lab/src:/app/shared-schemas/src:/app/shared"
ENV SPINALCORD_ROOT="/spinalcord"
ENV RHYTHM_STORAGE_ROOT="/rhythms"

CMD ["python", "-m", "rd_lab.autogen_runner"]

