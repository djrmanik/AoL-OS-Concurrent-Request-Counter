FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# cmd will be overridden by docker-compose for A vs B
CMD ["uvicorn", "main_a:app", "--host", "0.0.0.0", "--port", "8000"]
