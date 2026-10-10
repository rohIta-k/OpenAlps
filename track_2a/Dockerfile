FROM --platform=linux/amd64 python:3.11-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
# Phase 3: bake local models/indices here at BUILD time (nothing may be downloaded at run time):
# COPY models ./models
ENTRYPOINT ["python", "-m", "src.cli"]