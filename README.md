RetroArchPythonAPI
==================

A Python API for RetroArch (libretro)


Example Usage:

RETROAPI = RetroArch('/usr/bin/retroarch','settings','settings/bios','settings/controller')

RETROAPI.start(<Game Path>,<Libretro Plugin Path>)

RETROAPI.toggle_fullscreen()

RETROAPI.toggle_fullscreen()

RETROAPI.toggle_pause()

RETROAPI.toggle_pause()

save_state = RETROAPI.save()

RETROAPI.reset()

RETROAPI.load(save_state)

RETROAPI.quit()
