"""Botão GPIO compatível com libgpiod 1.x e 2.x."""

from __future__ import annotations

import threading
import time
from datetime import timedelta


class GPIOButton:
    """Transforma uma borda de descida do GPIO em eventos de pressionamento."""

    def __init__(self, chip_path: str, line_offset: int, debounce_ms: int = 120):
        try:
            import gpiod
        except ImportError as exc:
            raise RuntimeError(
                "gpiod não está instalado. Instale python3-libgpiod."
            ) from exc

        self._gpiod = gpiod
        self._chip_path = chip_path
        self._line_offset = line_offset
        self._debounce_seconds = debounce_ms / 1000.0
        self._last_press = 0.0
        self._pressed = threading.Event()
        self._stop = threading.Event()
        self._request = None
        self._line = None
        self._chip = None
        self._api_version = 2 if hasattr(gpiod, "request_lines") else 1

        if self._api_version == 2:
            self._setup_v2()
        else:
            self._setup_v1()

        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def _setup_v2(self) -> None:
        import gpiod

        try:
            from gpiod.line import Bias, Direction, Edge
        except ImportError:
            Bias = gpiod.Bias
            Direction = gpiod.Direction
            Edge = gpiod.Edge

        settings = gpiod.LineSettings(
            direction=Direction.INPUT,
            edge_detection=Edge.FALLING,
            bias=Bias.PULL_UP,
            debounce_period=timedelta(
                milliseconds=max(0, int(self._debounce_seconds * 1000))
            ),
        )
        self._request = gpiod.request_lines(
            self._chip_path,
            consumer="orangepi-camera-zoom",
            config={self._line_offset: settings},
        )

    def _setup_v1(self) -> None:
        gpiod = self._gpiod
        self._chip = gpiod.Chip(self._chip_path)
        self._line = self._chip.get_line(self._line_offset)
        flags = getattr(gpiod, "LINE_REQ_FLAG_BIAS_PULL_UP", 0)
        self._line.request(
            consumer="orangepi-camera-zoom",
            type=gpiod.LINE_REQ_EV_FALLING_EDGE,
            flags=flags,
        )

    def _register_press(self) -> None:
        now = time.monotonic()
        if now - self._last_press >= self._debounce_seconds:
            self._last_press = now
            self._pressed.set()

    def _read_loop(self) -> None:
        if self._api_version == 2:
            self._read_loop_v2()
        else:
            self._read_loop_v1()

    def _read_loop_v2(self) -> None:
        try:
            while not self._stop.is_set():
                events = self._request.read_edge_events()
                for event in events:
                    if self._stop.is_set():
                        return
                    event_type = getattr(event, "event_type", None)
                    falling = getattr(event_type, "name", "") == "FALLING_EDGE"
                    if falling or event_type is None:
                        self._register_press()
        except (OSError, RuntimeError, ValueError):
            if not self._stop.is_set():
                self._stop.set()

    def _read_loop_v1(self) -> None:
        try:
            while not self._stop.is_set():
                if not self._line.event_wait(sec=1):
                    continue
                self._line.event_read()
                self._register_press()
        except (OSError, RuntimeError, ValueError):
            if not self._stop.is_set():
                self._stop.set()

    def was_pressed(self) -> bool:
        """Retorna True uma vez para cada toque detectado."""
        if not self._pressed.wait(timeout=0):
            return False
        self._pressed.clear()
        return True

    def close(self) -> None:
        self._stop.set()
        try:
            if self._request is not None:
                self._request.release()
            if self._line is not None:
                self._line.release()
            if self._chip is not None:
                self._chip.close()
        except (OSError, RuntimeError, AttributeError):
            pass


class DisabledButton:
    """Implementação vazia para testar a câmera sem GPIO."""

    def was_pressed(self) -> bool:
        return False

    def close(self) -> None:
        pass


def create_button(
    enabled: bool,
    chip_path: str,
    line_offset: int,
    debounce_ms: int,
) -> GPIOButton | DisabledButton:
    if not enabled:
        return DisabledButton()
    return GPIOButton(chip_path, line_offset, debounce_ms)
