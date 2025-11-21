FROM python:3.11-slim

WORKDIR /app

# Install BaseX CLI for XQuery execution
RUN apt-get update && apt-get install -y basex && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "rpc_server.py"]
