"""Configuracao padrao da camera para a Lupa Digital."""
import os


CAMERA_DEVICE = os.getenv("CAMERA_DEVICE", "/dev/video1")
CAMERA_WIDTH = int(os.getenv("CAMERA_WIDTH", "1280"))
CAMERA_HEIGHT = int(os.getenv("CAMERA_HEIGHT", "720"))
CAMERA_FPS = int(os.getenv("CAMERA_FPS", "30"))
