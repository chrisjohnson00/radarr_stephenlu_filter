FROM python:3.11.0-slim

WORKDIR /usr/src/app
EXPOSE 5000

RUN apt update && \
    apt install -y curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD gunicorn --log-file=- --workers=2 --threads=4 --worker-class=gthread --worker-tmp-dir /dev/shm --bind 0.0.0.0:5000 app
