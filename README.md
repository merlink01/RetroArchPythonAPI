RetroArchPythonAPI
==================

A Python API for RetroArch (libretro)


Example Usage:

```
RETROAPI = RetroArch(retroarch_path='/usr/bin/retroarch',settings_path='settings')

RETROAPI.start("Game Path","Libretro Core Path")

RETROAPI.toggle_fullscreen()

RETROAPI.toggle_fullscreen()

RETROAPI.toggle_pause()

RETROAPI.toggle_pause()

save_state = RETROAPI.save()

RETROAPI.reset()

RETROAPI.load(save_state)

RETROAPI.stop()
```
