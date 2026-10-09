"""Padrões validados para Orange Pi 3 LTS; podem ser sobrescritos pelo ambiente."""
import os


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    return default if value is None else value.strip().lower() in {"1", "true", "yes", "sim", "on"}


CAMERA_DEVICE = os.getenv("CAMERA_DEVICE", "/dev/video1")
CAMERA_WIDTH = int(os.getenv("CAMERA_WIDTH", "1280"))
CAMERA_HEIGHT = int(os.getenv("CAMERA_HEIGHT", "720"))
CAMERA_FPS = int(os.getenv("CAMERA_FPS", "30"))
GPIO_ENABLED = env_bool("GPIO_ENABLED", True)
GPIO_CHIP = os.getenv("GPIO_CHIP", "/dev/gpiochip1")
GPIO_LINE = int(os.getenv("GPIO_LINE", "230"))
ZOOM_MAX = int(os.getenv("ZOOM_MAX", "8"))
BUTTON_DEBOUNCE_MS = int(os.getenv("BUTTON_DEBOUNCE_MS", "80"))
