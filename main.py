"""Visualizador de câmera 720p com zoom alternado por botão GPIO."""

from __future__ import annotations

import argparse
import sys
import time

import cv2

import config
from gpio_button import create_button


WINDOW_NAME = "Orange Pi Camera"


def center_zoom(frame, factor: float):
    if factor <= 1.0:
        return frame

    height, width = frame.shape[:2]
    crop_width = max(1, int(width / factor))
    crop_height = max(1, int(height / factor))
    left = max(0, (width - crop_width) // 2)
    top = max(0, (height - crop_height) // 2)
    cropped = frame[top : top + crop_height, left : left + crop_width]
    return cv2.resize(cropped, (width, height), interpolation=cv2.INTER_LINEAR)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--camera", default=config.CAMERA_DEVICE)
    parser.add_argument("--width", type=int, default=config.CAMERA_WIDTH)
    parser.add_argument("--height", type=int, default=config.CAMERA_HEIGHT)
    parser.add_argument("--fps", type=int, default=config.CAMERA_FPS)
    parser.add_argument("--gpio-chip", default=config.GPIO_CHIP)
    parser.add_argument("--gpio-line", type=int, default=config.GPIO_LINE)
    parser.add_argument("--zoom-factor", type=float, default=config.ZOOM_FACTOR)
    parser.add_argument("--debounce-ms", type=int, default=config.BUTTON_DEBOUNCE_MS)
    parser.add_argument("--no-gpio", action="store_true", help="desliga o botão físico")
    parser.add_argument("--windowed", action="store_true", help="não inicia em tela cheia")
    return parser.parse_args()


def open_camera(device: str, width: int, height: int, fps: int) -> cv2.VideoCapture:
    camera = cv2.VideoCapture(device, cv2.CAP_V4L2)
    if not camera.isOpened():
        camera.release()
        camera = cv2.VideoCapture(device)

    if not camera.isOpened():
        raise RuntimeError(f"Não foi possível abrir a câmera {device}.")

    # Buffer pequeno = menos atraso entre a cena real e a imagem exibida.
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    camera.set(cv2.CAP_PROP_FPS, fps)
    return camera


def run(args: argparse.Namespace) -> int:
    camera = open_camera(args.camera, args.width, args.height, args.fps)
    button = create_button(
        enabled=config.GPIO_ENABLED and not args.no_gpio,
        chip_path=args.gpio_chip,
        line_offset=args.gpio_line,
        debounce_ms=args.debounce_ms,
    )

    zoomed = False
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    if not args.windowed:
        cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                print("Aviso: não foi possível ler um frame; tentando novamente...", file=sys.stderr)
                time.sleep(0.05)
                continue

            if button.was_pressed():
                zoomed = not zoomed

            displayed = center_zoom(frame, args.zoom_factor if zoomed else 1.0)
            cv2.imshow(WINDOW_NAME, displayed)

            # waitKey é necessário para a janela processar eventos e também
            # permite testar o botão com Espaço sem adicionar outra interface.
            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q"), ord("Q")):
                break
            if key == 32:
                zoomed = not zoomed
    finally:
        button.close()
        camera.release()
        cv2.destroyAllWindows()

    return 0


def main() -> int:
    args = parse_args()
    try:
        return run(args)
    except KeyboardInterrupt:
        return 0
    except RuntimeError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
