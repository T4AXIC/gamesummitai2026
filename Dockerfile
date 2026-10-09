FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PERDE_AUDIT=/tmp/audit_log.jsonl

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY perde/ perde/
COPY eval/results.json eval/results.json
COPY app.py .
COPY .streamlit/ .streamlit/

# Run as a non-root user (also required by Hugging Face Spaces)
RUN useradd -m -u 1000 perde
USER perde

EXPOSE 8501
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
