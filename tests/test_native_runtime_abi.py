import ctypes as ct
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from tetris.learning._library import load_library
from tetris.learning._native_observation import NativeObservation


class NativeRuntimeAbiTests(unittest.TestCase):
    def library(self, version=1, size=None):
        return SimpleNamespace(**{
            name: Mock(return_value=value) for name, value in {
                "kt_abi_version": version,
                "kt_observation_size": ct.sizeof(NativeObservation) if size is None else size,
                "kt_create": 0, "kt_destroy": None, "kt_observe": 0,
                "kt_submit": 0, "kt_advance": 0,
            }.items()
        })

    def test_abi_version_mismatch_fails_before_state_creation(self):
        library = self.library(version=2)
        with patch("tetris.learning._library.ct.CDLL", return_value=library):
            with self.assertRaisesRegex(RuntimeError, "ABI version"):
                load_library(Path(__file__))
        library.kt_create.assert_not_called()

    def test_layout_mismatch_fails_before_state_creation(self):
        library = self.library(size=1)
        with patch("tetris.learning._library.ct.CDLL", return_value=library):
            with self.assertRaisesRegex(RuntimeError, "layout mismatch"):
                load_library(Path(__file__))
        library.kt_create.assert_not_called()
