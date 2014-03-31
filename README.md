RetroArchPythonAPI
==================

A Python API for RetroArch (libretro)


Example Usage:

RETROAPI = RetroArch(retroarch_path='/usr/bin/retroarch',settings_path='settings',bios_path='settings/bios',controller_path='settings/controller',resolution='800x600',start_fullscreen=True)


RETROAPI.start("Game Path","Libretro Plugin Path")

RETROAPI.toggle_fullscreen()

RETROAPI.toggle_fullscreen()

RETROAPI.toggle_pause()

RETROAPI.toggle_pause()

save_state = RETROAPI.save()

RETROAPI.reset()

RETROAPI.load(save_state)

RETROAPI.quit()
