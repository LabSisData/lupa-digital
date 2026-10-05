"""Configuração padrão do visualizador da câmera."""

import os


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "sim", "on"}


CAMERA_DEVICE = os.getenv("CAMERA_DEVICE", "/dev/video0")
CAMERA_WIDTH = int(os.getenv("CAMERA_WIDTH", "1280"))
CAMERA_HEIGHT = int(os.getenv("CAMERA_HEIGHT", "720"))
CAMERA_FPS = int(os.getenv("CAMERA_FPS", "30"))

GPIO_ENABLED = env_bool("GPIO_ENABLED", True)
GPIO_CHIP = os.getenv("GPIO_CHIP", "/dev/gpiochip0")
GPIO_LINE = int(os.getenv("GPIO_LINE", "6"))

ZOOM_FACTOR = float(os.getenv("ZOOM_FACTOR", "2.0"))
BUTTON_DEBOUNCE_MS = int(os.getenv("BUTTON_DEBOUNCE_MS", "120"))
