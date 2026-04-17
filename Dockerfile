# Stage 1: Builder
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt


# =================================================================
# Stage 2: Runtime
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# These libraries will be needed for pyvista and VTK
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libosmesa6 \
    libxcursor1 \
    libegl1 \
    && rm -rf /var/lib/apt/lists/*

# Install the Python dependencies from the builder stage
COPY --from=builder /install /usr/local

RUN useradd -m -u 1000 terrainforge

RUN mkdir -p /terrainforge
COPY . /terrainforge/

RUN chgrp -R 0 /terrainforge && \
    chmod -R g+rwX /terrainforge && \
    chmod -R a+rwX /terrainforge/images && \
    chmod -R a+rwX /terrainforge/graphs &&\
    chmod -R a+rwX /terrainforge/mesh

# set home, at leats bmi-topography needs it to store the cache, and it should be writable by any any user
ENV HOME=/tmp
ENV XDG_CACHE_HOME=/tmp/.cache

RUN mkdir -p /tmp/.cache && chmod -R 1777 /tmp

WORKDIR /terrainforge

USER terrainforge

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health', timeout=5).read()"

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "wsgi:application"]

