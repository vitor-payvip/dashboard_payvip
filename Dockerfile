# Dockerfile

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# <<< MUDANÇA: REMOVA A LINHA ABAIXO >>>
# ENV GOOGLE_APPLICATION_CREDENTIALS=/app/gcp-credentials.json

EXPOSE 8501

CMD ["python", "-m", "streamlit", "run", "dashboard.py", "--server.port", "8501", "--server.enableCORS", "false"]