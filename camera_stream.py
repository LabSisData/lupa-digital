"""Captura assíncrona: sempre exibe o quadro mais recente e recupera desconexões."""
from __future__ import annotations

import threading
import time

import cv2


def profiles(width: int, height: int, fps: int):
    """Prefere MJPEG 720p; recua para formatos/resoluções compatíveis."""
    return [
        ("MJPG", width, height, fps),
        ("YUYV", width, height, min(fps, 15)),
        (None, width, height, min(fps, 15)),
        (None, 640, 480, 15),
        (None, None, None, None),
    ]


class CameraStream:
    def __init__(self, device: str, width: int, height: int, fps: int):
        self.device, self.width, self.height, self.fps = device, width, height, fps
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._frame = None
        self._timestamp = 0.0
        self._sequence = 0
        self.status = "Iniciando câmera..."
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _open(self):
        for fourcc, width, height, fps in profiles(self.width, self.height, self.fps):
            if self._stop.is_set():
                break
            cap = cv2.VideoCapture(self.device, cv2.CAP_V4L2)
            if not cap.isOpened():
                cap.release()
                continue
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            if fourcc:
                cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*fourcc))
            if width:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            if height:
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            if fps:
                cap.set(cv2.CAP_PROP_FPS, fps)
            for _ in range(8):
                ok, frame = cap.read()
                if ok and frame is not None and frame.size:
                    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    self.status = f"Câmera {self.device}: {actual_w}x{actual_h} ({fourcc or 'padrão'})"
                    with self._lock:
                        self._frame = frame
                        self._timestamp = time.monotonic()
                        self._sequence += 1
                    return cap
                time.sleep(0.03)
            cap.release()
        return None

    def _worker(self):
        while not self._stop.is_set():
            cap = self._open()
            if cap is None:
                self.status = f"Sem imagem em {self.device}. Verifique conexão e formatos."
                self._stop.wait(1.0)
                continue
            failed = 0
            try:
                while not self._stop.is_set():
                    ok, frame = cap.read()
                    if ok and frame is not None and frame.size:
                        failed = 0
                        with self._lock:
                            self._frame = frame
                            self._timestamp = time.monotonic()
                            self._sequence += 1
                    else:
                        failed += 1
                        self._stop.wait(0.05)
                        if failed >= 12:
                            self.status = "Câmera sem resposta; reconectando..."
                            break
            finally:
                cap.release()

    def latest(self):
        with self._lock:
            return self._frame, self._timestamp, self._sequence

    def close(self):
        self._stop.set()
        self._thread.join(timeout=2.0)
