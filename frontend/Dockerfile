FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY frontend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY frontend/ /app/

ENV API_BASE_URL=http://backend:8000

EXPOSE 8501

CMD ["streamlit", "run", "app_collaborative.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
