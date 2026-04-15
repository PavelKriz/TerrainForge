FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    curl \
    gdal-bin \
    libgdal-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libxcb-xinerama0 \
    libxkbcommon-x11-0 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 CMD curl -fsS http://localhost:8000/health || exit 1

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

RUN useradd -m -u 1000 terrainforge && \
    mkdir -p /var/lib/terrainforge && \
    chown -R terrainforge:terrainforge /var/lib/terrainforge /app

COPY --chown=terrainforge:terrainforge . /var/lib/terrainforge/

WORKDIR /var/lib/terrainforge

USER terrainforge

EXPOSE 8000

# TODO document to mount secrets and or config
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "wsgi:application"]


