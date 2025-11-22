FROM nvidia/cuda:11.6.2-cudnn8-runtime-ubuntu20.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    wget \
    curl \
    git \
    unzip \
    zip \
    net-tools \
    procps \
    tmux \
    rsync \
    vim \
    tree \
    xdg-utils \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip

RUN pip3 install torch==1.13.1+cu116 \
    torchvision==0.14.1+cu116 \
    torchaudio==0.13.1 \
    --extra-index-url https://download.pytorch.org/whl/cu116

RUN pip3 install pyg_lib torch_scatter torch_sparse torch_cluster torch_spline_conv \
    -f https://data.pyg.org/whl/torch-1.13.0+cu116.html

RUN mkdir -p /workplace
WORKDIR /workplace

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .
RUN pip3 install --no-cache-dir \
    fastapi uvicorn python-multipart httpx torch_geometric

RUN apt-get update && apt-get install -y supervisor && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /var/log/supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

ENV PYTHONUNBUFFERED=1
ENV ANONYMIZED_TELEMETRY=false

# Expose port
EXPOSE 8000

# Supervisor start
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
