FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY src/ ./src/

WORKDIR /app/src

CMD ["python", "-m", "bot"]