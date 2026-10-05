#!/usr/bin/env bash
set -euo pipefail

echo "Instalando requisitos do Orange Pi..."
sudo apt update
sudo apt install -y python3 python3-opencv python3-libgpiod gpiod v4l-utils

if id -nG "$USER" | tr ' ' '\n' | grep -qx video; then
  echo "O usuário já está no grupo video."
else
  sudo usermod -aG video "$USER"
  echo "O usuário foi adicionado ao grupo video. Faça logout/login antes de executar."
fi

echo "Instalação concluída. Use: python3 main.py --no-gpio"
