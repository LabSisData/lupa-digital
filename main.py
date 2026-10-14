"""Lupa Digital para Orange Pi 3 LTS com zoom fixo de 3x."""
from __future__ import annotations

import argparse
import sys
import time

import cv2
import numpy as np

import config
from camera_stream import CameraStream

WINDOW = "Lupa Digital - Orange Pi"
FIXED_ZOOM = 3


def center_zoom(frame, factor: float):
    if factor <= 1.0:
        return frame
    h, w = frame.shape[:2]
    cut_w, cut_h = max(1, round(w / factor)), max(1, round(h / factor))
    x, y = (w - cut_w) // 2, (h - cut_h) // 2
    return cv2.resize(
        frame[y:y + cut_h, x:x + cut_w],
        (w, h),
        interpolation=cv2.INTER_LINEAR,
    )


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--camera", default=config.CAMERA_DEVICE)
    p.add_argument("--width", type=int, default=config.CAMERA_WIDTH)
    p.add_argument("--height", type=int, default=config.CAMERA_HEIGHT)
    p.add_argument("--fps", type=int, default=config.CAMERA_FPS)
    p.add_argument("--windowed", action="store_true")
    return p.parse_args(argv)


def status_screen(message: str):
    frame = np.zeros((360, 640, 3), dtype=np.uint8)
    cv2.putText(
        frame,
        "Lupa Digital - Orange Pi",
        (30, 115),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.85,
        (240, 240, 240),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        message[:65],
        (30, 185),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (170, 210, 255),
        1,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        "Zoom fixo: 3x | ESC/Q: sair",
        (30, 240),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (180, 180, 180),
        1,
        cv2.LINE_AA,
    )
    return frame


def run(args):
    if args.width < 1 or args.height < 1 or args.fps < 1:
        raise ValueError("Largura, altura e FPS devem ser positivos")

    camera = None
    try:
        camera = CameraStream(args.camera, args.width, args.height, args.fps)
        cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
        cv2.imshow(WINDOW, status_screen("Aguardando primeiro quadro da camera..."))
        cv2.waitKey(1)

        if args.windowed:
            cv2.resizeWindow(WINDOW, 960, 540)
        else:
            cv2.setWindowProperty(
                WINDOW,
                cv2.WND_PROP_FULLSCREEN,
                cv2.WINDOW_FULLSCREEN,
            )

        last_seq = -1
        last_status = 0.0

        while True:
            frame, timestamp, seq = camera.latest()
            now = time.monotonic()

            if frame is not None and now - timestamp < 1.5:
                if seq != last_seq:
                    displayed = center_zoom(frame, FIXED_ZOOM)
                    cv2.putText(
                        displayed,
                        "3x",
                        (15, 35),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.9,
                        (0, 220, 70),
                        2,
                        cv2.LINE_AA,
                    )
                    cv2.imshow(WINDOW, displayed)
                    last_seq = seq
            elif now - last_status >= 0.5:
                cv2.imshow(WINDOW, status_screen(camera.status))
                last_status = now
                last_seq = -1

            key = cv2.waitKey(15) & 0xFF
            if key in (27, ord("q"), ord("Q")):
                break

        return 0
    finally:
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
