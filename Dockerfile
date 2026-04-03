FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir requests beautifulsoup4

COPY hardverapro_monitor.py .

CMD ["python", "-u", "hardverapro_monitor.py"]
