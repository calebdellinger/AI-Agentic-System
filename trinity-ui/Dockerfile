FROM python:3.11-slim

WORKDIR /app

COPY trinity-ui/requirements.txt /app/trinity-ui/requirements.txt
COPY trinity-ui/app.py /app/trinity-ui/app.py
COPY trinity-ui/.streamlit /app/trinity-ui/.streamlit

RUN python -m pip install --no-cache-dir -U pip \
  && python -m pip install --no-cache-dir -r /app/trinity-ui/requirements.txt

EXPOSE 8501

ENV SPINALCORD_ROOT=/spinalcord

CMD ["streamlit", "run", "/app/trinity-ui/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
