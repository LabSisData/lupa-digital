"""Lupa Digital para Orange Pi 3 LTS: câmera fluida, zoom por botão e teclado."""
from __future__ import annotations

import argparse
import sys
import time

import cv2
import numpy as np

import config
from camera_stream import CameraStream
from gpio_button import DisabledButton, create_button

WINDOW = "Lupa Digital - Orange Pi"


def center_zoom(frame, factor: float):
    if factor <= 1.0:
        return frame
    h, w = frame.shape[:2]
    cut_w, cut_h = max(1, round(w / factor)), max(1, round(h / factor))
    x, y = (w - cut_w) // 2, (h - cut_h) // 2
    return cv2.resize(frame[y:y+cut_h, x:x+cut_w], (w, h), interpolation=cv2.INTER_LINEAR)


def next_zoom_level(current: int, max_zoom: int = 8) -> int:
    """Cada toque avança um nível; após o máximo, volta para a imagem normal."""
    if max_zoom < 2:
        raise ValueError("O zoom máximo deve ser pelo menos 2x")
    return 1 if current >= max_zoom else current + 1


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--camera", default=config.CAMERA_DEVICE)
    p.add_argument("--width", type=int, default=config.CAMERA_WIDTH)
    p.add_argument("--height", type=int, default=config.CAMERA_HEIGHT)
    p.add_argument("--fps", type=int, default=config.CAMERA_FPS)
    p.add_argument("--gpio-chip", default=config.GPIO_CHIP)
    p.add_argument("--gpio-line", type=int, default=config.GPIO_LINE)
    p.add_argument("--max-zoom", "--zoom-factor", dest="max_zoom", type=int,
                   default=config.ZOOM_MAX,
                   help="zoom máximo; cada toque avança 1x até o máximo (padrão: 8)")
    p.add_argument("--debounce-ms", type=int, default=config.BUTTON_DEBOUNCE_MS)
    p.add_argument("--no-gpio", action="store_true")
    p.add_argument("--windowed", action="store_true")
    return p.parse_args(argv)


def status_screen(message: str):
    frame = np.zeros((360, 640, 3), dtype=np.uint8)
    cv2.putText(frame, "Lupa Digital - Orange Pi", (30, 115),
                cv2.FONT_HERSHEY_SIMPLEX, 0.85, (240, 240, 240), 2, cv2.LINE_AA)
    cv2.putText(frame, message[:65], (30, 185),
                cv2.FONT_HERSHEY_SIMPLEX, 0.48, (170, 210, 255), 1, cv2.LINE_AA)
    cv2.putText(frame, "ESC/Q: sair | ESPACO: zoom", (30, 240),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1, cv2.LINE_AA)
    return frame


def run(args):
    if args.max_zoom < 2 or args.width < 1 or args.height < 1 or args.fps < 1:
        raise ValueError("Zoom máximo deve ser >= 2; largura, altura e FPS devem ser positivos")

    button = DisabledButton()
    camera = None
    try:
        if config.GPIO_ENABLED and not args.no_gpio:
            try:
                button = create_button(True, args.gpio_chip, args.gpio_line, args.debounce_ms)
                print(f"Botão conectado: {args.gpio_chip} linha {args.gpio_line}")
            except (OSError, ValueError, RuntimeError) as exc:
                print(f"Aviso: botão não disponível: {exc}. Use ESPAÇO para zoom.", file=sys.stderr)

        camera = CameraStream(args.camera, args.width, args.height, args.fps)
        cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
        cv2.imshow(WINDOW, status_screen("Aguardando primeiro quadro da câmera..."))
        cv2.waitKey(1)
        if args.windowed:
            cv2.resizeWindow(WINDOW, 960, 540)
        else:
            cv2.setWindowProperty(WINDOW, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        zoom_level = 1
        last_seq = -1
        last_status = 0.0
        while True:
            if button.was_pressed():
                zoom_level = next_zoom_level(zoom_level, args.max_zoom)
                last_seq = -1
                print(f"Zoom: {zoom_level}x")
            error = button.status_error()
            if error:
                print(f"Aviso: GPIO parou: {error}", file=sys.stderr)
                button.close()
                button = DisabledButton()

            frame, timestamp, seq = camera.latest()
            now = time.monotonic()
            if frame is not None and now - timestamp < 1.5:
                if seq != last_seq:
                    displayed = center_zoom(frame, zoom_level)
                    cv2.putText(displayed, f"{zoom_level}x",
                                (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.9,
                                (0, 220, 70), 2, cv2.LINE_AA)
                    cv2.imshow(WINDOW, displayed)
                    last_seq = seq
            elif now - last_status >= 0.5:
                cv2.imshow(WINDOW, status_screen(camera.status))
                last_status = now
                last_seq = -1

            key = cv2.waitKey(15) & 0xFF
            if key in (27, ord("q"), ord("Q")):
                break
            if key == 32:
                zoom_level = next_zoom_level(zoom_level, args.max_zoom)
                last_seq = -1
                print(f"Zoom: {zoom_level}x")
        return 0
    finally:
        button.close()
        if camera is not None:
            camera.close()
        cv2.destroyAllWindows()


def main():
    try:
        return run(parse_args())
    except (RuntimeError, ValueError, cv2.error) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
