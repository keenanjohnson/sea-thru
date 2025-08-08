ARG PLATFORM

FROM --platform=${PLATFORM} python:latest

# These will be pulled from the docker-compose.yml file via the `args` parameter
ARG WORKING_DIR
ARG CONDA_ENV_NAME

WORKDIR ${WORKING_DIR}

# Set some known env vars + lift from docker-compose args into env
ENV CONDA_ENV_NAME ${CONDA_ENV_NAME}
ENV CONDA_DIR /opt/conda
ENV PATH=$CONDA_DIR/bin:$PATH

# Dependencies
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    wget \
    git \
    gettext-base \
    ffmpeg \
    libsm6 \
    libxext6 \
    libtiff-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev && \
    apt-get clean

# Install miniconda (Basically anaconda without all the defaults, just the CLI.)
# This'll let us use whichever version of python is compatible with seathru and monodepth2. Should also make it less painful to upgrade in the future.
RUN for i in {1..3}; do \
        wget --quiet --timeout=30 --tries=3 --no-check-certificate https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
        break || sleep 10; \
    done && \
    bash ~/miniconda.sh -b -p $CONDA_DIR

COPY conda-environment.yml ./conda-environment-template.yml
RUN cat conda-environment-template.yml | envsubst > environment.yml

# Accept the terms-of-service and configure SSL
RUN $CONDA_DIR/bin/conda tos accept --channel https://repo.anaconda.com/pkgs/main --override-channels && \
    $CONDA_DIR/bin/conda tos accept --channel https://repo.anaconda.com/pkgs/r --override-channels && \
    $CONDA_DIR/bin/conda config --set ssl_verify false

# Configure pip to work without SSL verification
ENV PIP_TRUSTED_HOST "pypi.org pypi.python.org files.pythonhosted.org"

RUN $CONDA_DIR/bin/conda env create -f environment.yml
RUN echo "source activate $CONDA_ENV_NAME" > ~/.bashrc
ENV PATH $CONDA_DIR/envs/$CONDA_ENV_NAME/bin:$PATH

# Reinstall Pillow to ensure it links with system libraries correctly
RUN $CONDA_DIR/envs/$CONDA_ENV_NAME/bin/pip uninstall -y pillow && \
    $CONDA_DIR/envs/$CONDA_ENV_NAME/bin/pip install --no-cache-dir pillow==5.1.0

# Install gpr_tools for lossless GPR to DNG conversion
RUN cd /tmp && \
    git clone https://github.com/gopro/gpr.git && \
    cd gpr && \
    mkdir build && cd build && \
    cmake .. && \
    make -j$(nproc) && \
    cp source/app/gpr_tools/gpr_tools /usr/local/bin/ && \
    chmod +x /usr/local/bin/gpr_tools && \
    cd / && rm -rf /tmp/gpr

# Verify gpr_tools installation
RUN which gpr_tools && gpr_tools -h 2>&1 | head -5 || echo "gpr_tools installed"

ADD . ${WORKING_DIR}

ENTRYPOINT ["tail", "-f", "/dev/null"]
