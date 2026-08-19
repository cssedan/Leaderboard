FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY . .

CMD ["sh", "-c", "streamlit run leaderboard.py --server.address=0.0.0.0 --server.port=${PORT:-8501} --server.headless=true"]