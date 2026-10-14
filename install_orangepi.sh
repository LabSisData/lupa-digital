#!/usr/bin/env bash
set -euo pipefail

sudo apt update
sudo apt install -y python3 python3-opencv python3-numpy v4l-utils

sudo usermod -aG video "$USER"

echo 'Instalacao concluida. Encerre a sessao e entre novamente (ou reinicie).'
echo 'Depois execute: python3 main.py'
