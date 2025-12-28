FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements-server.txt .
RUN pip3 install --no-cache-dir -r requirements-server.txt && \
    pip3 cache purge && \
    rm -rf /root/.cache/pip

COPY detect.py ./
COPY server_flask.py server.py
COPY model/ ./model/

EXPOSE 8750

CMD ["python3", "/app/server.py"]

