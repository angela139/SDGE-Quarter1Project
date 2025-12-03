# 1) Choose base container

# Base notebook, contains Jupyter and relevant tools
# See https://github.com/ucsd-ets/datahub-docker-stack/wiki/Stable-Tag 
# for a list of the most current containers UCSD maintains
ARG BASE_CONTAINER=ghcr.io/ucsd-ets/datascience-notebook:stable

FROM $BASE_CONTAINER

LABEL maintainer="UC San Diego ITS/ETS <ets-consult@ucsd.edu>"
LABEL description="SDGE Technician Utilization Analysis Environment"

# 2) Change to root to install system packages
USER root

# 3) Install packages using notebook user
USER jovyan

# Install Python packages from requirements.txt
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Set working directory
WORKDIR /home/jovyan

# Override command to disable running jupyter notebook at launch
CMD ["/bin/bash"]
