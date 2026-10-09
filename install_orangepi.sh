#!/usr/bin/env bash
set -euo pipefail

sudo apt update
sudo apt install -y python3 python3-opencv python3-numpy python3-libgpiod gpiod v4l-utils

sudo groupadd -f gpio
sudo usermod -aG gpio,video "$USER"

printf '%s\n' 'SUBSYSTEM=="gpio", KERNEL=="gpiochip*", GROUP="gpio", MODE="0660"' | \
  sudo tee /etc/udev/rules.d/99-lupa-digital-gpio.rules >/dev/null
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=gpio || true

echo 'Instalação concluída. Encerre a sessão e entre novamente (ou reinicie)'
echo 'Depois execute: python3 main.py'
