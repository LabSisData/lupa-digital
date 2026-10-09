"""Leitura por polling de botão ativo em LOW (GND), libgpiod 1.x e 2.x.

O polling evita dependência de suporte a interrupções de borda no driver.
Um clique é gerado quando o sinal fica LOW de maneira estável.
"""
from __future__ import annotations

import threading
import time


class PressDetector:
    """Debounce de borda: uma ativação a cada ciclo de pressionar/soltar."""

    def __init__(self, debounce_ms: int = 80):
        self.delay = max(10, debounce_ms) / 1000.0
        self.stable = True  # HIGH: botão solto (pull-up)
        self.candidate = None
        self.changed_at = 0.0

    def update(self, high: bool, now: float) -> bool:
        if high == self.stable:
            self.candidate = None
            return False
        if self.candidate != high:
            self.candidate = high
            self.changed_at = now
            return False
        if now - self.changed_at < self.delay:
            return False
        self.stable = high
        self.candidate = None
        return not high


class GPIOButton:
    def __init__(self, chip_path: str, line_offset: int, debounce_ms: int = 80):
        try:
            import gpiod
        except ImportError as exc:
            raise RuntimeError("Instale python3-libgpiod para ler o botão") from exc

        self._chip_path = chip_path
        self._line_offset = line_offset
        self._chip = None
        self._line = None
        self._request = None
        self._stop = threading.Event()
        self._pressed = threading.Event()
        self._detector = PressDetector(debounce_ms)
        self._error = None
        self._gpiod = gpiod
        self._v2 = hasattr(gpiod, "request_lines")

        try:
            if self._v2:
                self._setup_v2()
            else:
                self._setup_v1()
        except (OSError, ValueError, RuntimeError) as exc:
            self.close()
            raise RuntimeError(
                f"Não foi possível configurar {chip_path}, linha {line_offset}: {exc}"
            ) from exc

        self._thread = threading.Thread(target=self._poll, daemon=True)
        self._thread.start()

    def _setup_v2(self):
        from gpiod.line import Bias, Direction
        gpiod = self._gpiod
        for bias in (Bias.PULL_UP, Bias.AS_IS):
            try:
                self._request = gpiod.request_lines(
                    self._chip_path,
                    consumer="lupa-digital",
                    config={self._line_offset: gpiod.LineSettings(
                        direction=Direction.INPUT, bias=bias
                    )},
                )
                if bias == Bias.AS_IS:
                    print("Aviso: pull-up interno indisponível. Use resistor de 10 kΩ para 3,3 V.")
                return
            except (OSError, ValueError):
                if bias == Bias.AS_IS:
                    raise

    def _setup_v1(self):
        gpiod = self._gpiod
        self._chip = gpiod.Chip(self._chip_path)
        self._line = self._chip.get_line(self._line_offset)
        for flags in (getattr(gpiod, "LINE_REQ_FLAG_BIAS_PULL_UP", 0), 0):
            try:
                self._line.request(consumer="lupa-digital", type=gpiod.LINE_REQ_DIR_IN, flags=flags)
                if flags == 0:
                    print("Aviso: confirme o pull-up do GPIO; resistor externo 10 kΩ pode ser necessário.")
                return
            except (OSError, ValueError):
                if flags == 0:
                    raise

    def _read_high(self) -> bool:
        if self._v2:
            value = self._request.get_value(self._line_offset)
            return int(getattr(value, "value", value)) == 1
        return self._line.get_value() == 1

    def _poll(self):
        try:
            while not self._stop.wait(0.015):
                if self._detector.update(self._read_high(), time.monotonic()):
                    self._pressed.set()
        except (OSError, ValueError, RuntimeError) as exc:
            self._error = str(exc)
            self._stop.set()

    def was_pressed(self) -> bool:
        if self._pressed.is_set():
            self._pressed.clear()
            return True
        return False

    def status_error(self) -> str | None:
        return self._error

    def close(self):
        self._stop.set()
        for obj, method in ((self._request, "release"), (self._line, "release"), (self._chip, "close")):
            if obj is not None:
                try:
                    getattr(obj, method)()
                except (OSError, ValueError, RuntimeError):
                    pass
        self._request = self._line = self._chip = None


class DisabledButton:
    def was_pressed(self) -> bool:
        return False

    def status_error(self) -> str | None:
        return None

    def close(self):
        pass


def create_button(enabled: bool, chip_path: str, line_offset: int, debounce_ms: int):
    if not enabled:
        return DisabledButton()
    return GPIOButton(chip_path, line_offset, debounce_ms)
