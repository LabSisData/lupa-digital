"""Testes sem câmera, desktop ou GPIO físico."""
import unittest
import threading
from unittest import mock

import numpy as np

from camera_stream import CameraStream, profiles
from gpio_button import PressDetector
from main import center_zoom, next_zoom_level, parse_args


class LupaTests(unittest.TestCase):
    def test_defaults_orangepi(self):
        args = parse_args([])
        self.assertEqual(args.camera, "/dev/video1")
        self.assertEqual(args.gpio_chip, "/dev/gpiochip1")
        self.assertEqual(args.gpio_line, 230)

    def test_zoom_changes_central_crop(self):
        image = np.arange(4 * 4 * 3, dtype=np.uint8).reshape(4, 4, 3)
        self.assertIs(center_zoom(image, 1), image)
        zoomed = center_zoom(image, 2)
        self.assertEqual(zoomed.shape, image.shape)
        np.testing.assert_array_equal(zoomed[0, 0], image[1, 1])

    def test_zoom_cycle_to_eight_and_back(self):
        level = 1
        levels = []
        for _ in range(9):
            level = next_zoom_level(level, 8)
            levels.append(level)
        self.assertEqual(levels, [2, 3, 4, 5, 6, 7, 8, 1, 2])

    def test_zoom_maximum_option_and_alias(self):
        self.assertEqual(parse_args([]).max_zoom, 8)
        self.assertEqual(parse_args(["--max-zoom", "5"]).max_zoom, 5)
        self.assertEqual(parse_args(["--zoom-factor", "6"]).max_zoom, 6)
        self.assertEqual(next_zoom_level(3, 3), 1)
        with self.assertRaises(ValueError):
            next_zoom_level(1, 1)

    def test_zoom_eight_keeps_frame_size(self):
        image = np.zeros((72, 128, 3), dtype=np.uint8)
        self.assertEqual(center_zoom(image, 8).shape, image.shape)

    def test_capture_profiles_have_fallback(self):
        p = profiles(1280, 720, 30)
        self.assertEqual(p[0], ("MJPG", 1280, 720, 30))
        self.assertIn((None, 640, 480, 15), p)

    def test_button_debounce_ignores_bounce_and_hold(self):
        d = PressDetector(50)
        self.assertFalse(d.update(True, 0))
        self.assertFalse(d.update(False, 0.01))
        self.assertFalse(d.update(True, 0.02))
        self.assertFalse(d.update(False, 0.03))
        self.assertTrue(d.update(False, 0.09))
        self.assertFalse(d.update(False, 0.30))
        self.assertFalse(d.update(True, 0.31))
        self.assertFalse(d.update(True, 0.37))
        self.assertFalse(d.update(False, 0.4))
        self.assertTrue(d.update(False, 0.46))

    def test_camera_tries_another_format_after_failed_frames(self):
        """Se MJPEG falhar, tenta YUYV antes de desistir da câmera."""
        bad = mock.Mock()
        good = mock.Mock()
        bad.isOpened.return_value = True
        good.isOpened.return_value = True
        bad.read.return_value = (False, None)
        good.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        good.get.side_effect = [640, 480]
        stream = CameraStream.__new__(CameraStream)
        stream.device = "/dev/video1"
        stream.width, stream.height, stream.fps = 1280, 720, 30
        stream._stop = threading.Event()
        stream._lock = threading.Lock()
        stream._frame = None
        stream._timestamp = 0.0
        stream._sequence = 0
        with mock.patch("camera_stream.cv2.VideoCapture", side_effect=[bad, good]), \
             mock.patch("camera_stream.time.sleep", return_value=None):
            opened = stream._open()
        self.assertIs(opened, good)
        self.assertTrue(bad.release.called)
        self.assertEqual(stream._sequence, 1)
        self.assertEqual(stream.latest()[0].shape, (480, 640, 3))


if __name__ == "__main__":
    unittest.main()
