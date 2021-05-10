#!/usr/bin/env bash

# FIRST VERIFY NVIDIA DRIVER IS INSTALLED: $nvidia-smi
# OR
# lspci | grep -i nvidia

# setup the nvidia-container-runtime repository (https://nvidia.github.io/nvidia-container-runtime/)
curl -s -L https://nvidia.github.io/nvidia-container-runtime/gpgkey | \
  sudo apt-key add -
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-container-runtime/$distribution/nvidia-container-runtime.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-runtime.list
sudo apt-get update

apt-get install nvidia-container-runtime

# Ensure the nvidia-container-runtime-hook is accessible from $PATH
which nvidia-container-runtime-hook

# test that GPUs are accessible from docker:
docker run -it --rm --gpus all ubuntu nvidia-smi
