#!/usr/bin/env python

"""Test Routine for RetroArchPythonApi"""

import sys
import logging
import unittest
from retroarchpythonapi import RetroArchPythonApi

RETROARCH_PATH = '/usr/bin/retroarch'
ROM_TO_TEST = "~/Games/Super Nintendo Entertainment System/acme.smc"
CORE_TO_TEST = '/usr/lib/libretro/snes9x_libretro.so'
TEST_PATH = '/tmp/test'


class API_TEST(unittest.TestCase):

    def test_00_START_STOP(self):
        api = RetroArchPythonApi(retroarch_path=RETROARCH_PATH,
                                 settings_path=TEST_PATH,
                                 fullscreen=False)
        answer = api.start(ROM_TO_TEST, CORE_TO_TEST)
        assert answer
        api.stop()

    def test_01_pause(self):

        api = RetroArchPythonApi(retroarch_path=RETROARCH_PATH,
                                 settings_path=TEST_PATH,
                                 fullscreen=False)
        api.start(ROM_TO_TEST, CORE_TO_TEST)
        assert api.toggle_pause() == 'paused'
        assert api.toggle_pause() == 'unpaused'

        api.stop()

    def test_02_fullscreen(self):

        api = RetroArchPythonApi(retroarch_path=RETROARCH_PATH,
                                 settings_path=TEST_PATH,
                                 fullscreen=False)
        api.start(ROM_TO_TEST, CORE_TO_TEST)
        assert api.toggle_fullscreen() == 'fullscreen'
        assert api.toggle_fullscreen() == 'window'

        api.stop()

    def test_03_reset(self):

        api = RetroArchPythonApi(retroarch_path=RETROARCH_PATH,
                                 settings_path=TEST_PATH,
                                 fullscreen=False)
        api.start(ROM_TO_TEST, CORE_TO_TEST)

        assert api.reset()

        api.stop()

    def test_04_save_load(self):

        api = RetroArchPythonApi(retroarch_path=RETROARCH_PATH,
                                 settings_path=TEST_PATH,
                                 fullscreen=False)
        api.start(ROM_TO_TEST, CORE_TO_TEST)

        savegame = api.save()
        assert savegame
        assert api.load(savegame)

        api.stop()

if __name__ == "__main__":

    logger = logging.getLogger()
    fmt_string = "[%(levelname)-7s]%(asctime)s.%(msecs)-3d\
    %(module)s[%(lineno)-3d]/%(funcName)-10s  %(message)-8s "
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(fmt_string, "%H:%M:%S"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    unittest.main()
