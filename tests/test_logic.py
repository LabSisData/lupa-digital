"""Testes sem camera ou desktop fisico."""
import threading
import unittest
from unittest import mock

import numpy as np

from camera_stream import CameraStream, profiles
from main import FIXED_ZOOM, center_zoom, parse_args


class LupaTests(unittest.TestCase):
    def test_defaults_orangepi(self):
        args = parse_args([])
        self.assertEqual(args.camera, "/dev/video1")
        self.assertEqual(args.width, 1280)
        self.assertEqual(args.height, 720)
        self.assertEqual(args.fps, 30)

    def test_zoom_is_fixed_at_three(self):
        self.assertEqual(FIXED_ZOOM, 3)

    def test_zoom_three_changes_central_crop_and_keeps_size(self):
        image = np.arange(9 * 9 * 3, dtype=np.uint8).reshape(9, 9, 3)
        zoomed = center_zoom(image, FIXED_ZOOM)
        self.assertEqual(zoomed.shape, image.shape)
        np.testing.assert_array_equal(zoomed[0, 0], image[3, 3])

    def test_capture_profiles_have_fallback(self):
        p = profiles(1280, 720, 30)
        self.assertEqual(p[0], ("MJPG", 1280, 720, 30))
        self.assertIn((None, 640, 480, 15), p)

    def test_camera_tries_another_format_after_failed_frames(self):
        """Se MJPEG falhar, tenta YUYV antes de desistir da camera."""
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
