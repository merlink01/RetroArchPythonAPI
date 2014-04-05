#!/usr/bin/env python

"""Retroarch Python API
This is a Python API for the RetroArch /
libretro Libraries for Console Emulators
Target:
Create an easy to use API to implement it in your own UI
"""

import os
import time
import Queue
import logging
import threading
import subprocess

__version__ = 0.02
__copyright__ = 'GPL V2'


class RetroArchPythonApi(object):

    """Usage:
    api = RetroArch(retroarch_path='<Path>',settings_path='<Path>')
    #Options:
    #retroarch_path='/usr/bin/retroarch' --> path to retroarch executable
    #settings_path='settings' --> path where all settings are saved
    #resolution=('800x600') --> Setup the Resulution
    #Default=800x600
    #fullscreen=('fullscreen') --> Startup in fullscreen mode
    #Default=True

    api.start(<Game Path>,<Libretro Plugin Path>)
    api.toggle_pause()
    save_state = api.save()
    api.reset()
    api.load(save_state)
    api.stop()
    """

    _stderr_queue = Queue.Queue()
    rom_path = None

    _fullscreen = None
    _process = None
    _running = False
    _pause = False

    def __init__(self, **kwargs):

        # Logging
        self.logger = logging.getLogger('RetroArchPythonApi')

        # Settings
        self.settings = {}
        if 'resolution' in kwargs:
            self.settings['resolution'] = kwargs['resolution']
        else:
            self.settings['resolution'] = '800x600'

        if 'fullscreen' in kwargs:
            self.settings['fullscreen'] = kwargs['fullscreen']
        else:
            self.settings['fullscreen'] = True

        # Pathes
        self.pathes = {}

        # RetroArch Executable Path
        assert 'retroarch_path' in kwargs, 'RetroArch Path must be set.'
        retroarch_path = os.path.abspath(kwargs['retroarch_path'])
        assert os.path.isfile(retroarch_path),\
            'RetroArch execuatable not found'
        self.pathes['retroarch_path'] = retroarch_path

        # Settings Path
        assert 'settings_path' in kwargs
        settings_path = os.path.abspath(kwargs['settings_path'])
        self.pathes['settings'] = settings_path
        if not os.path.isdir(settings_path):
            os.makedirs(settings_path)

        # Bios Path
        bios_path = os.path.join(self.pathes['settings'], 'bios')
        self.pathes['bios'] = bios_path
        if not os.path.isdir(bios_path):
            os.makedirs(bios_path)

        # Controller Autoconfig Path
        controller_path = os.path.join(self.pathes['settings'], 'controller')
        self.pathes['controller'] = controller_path
        if not os.path.isdir(controller_path):
            os.makedirs(controller_path)

        # RetroArch Config File
        configfile = os.path.join(settings_path, 'retroarch.cfg')
        self.pathes['configfile'] = configfile
        self._create_configfile()

        # Start Check Alive Thread
        cath = threading.Thread(target=self._thread_check_alive)
        cath.daemon = True
        cath.start()

        self.logger.info('Starting Retroarch Python API (Version:%s)'
                         % __version__)
        self.logger.debug('Start in Fullscreen: %s'
                          % self.settings['fullscreen'])
        self.logger.debug('Resolution: %s'
                          % self.settings['resolution'])
        self.logger.debug('RetroArch Path: %s' % retroarch_path)
        self.logger.debug('Settings Path: %s'
                          % self.pathes['settings'])
        self.logger.debug('Bios Path: %s'
                          % self.pathes['bios'])
        self.logger.debug('Gamecontroller Path: %s'
                          % self.pathes['controller'])

    def _thread_stderr_read(self):

        """Read the output from retroarch stderr
        and put it to self.stderr.queue"""

        while 1:
            try:
                line = self._process.stderr.readline().rstrip()

                if 'checkalive' in line:
                    continue

                self.logger.debug(line)

            except:
                self._running = False
                self._stderr_queue.put('error')
                break

            self._stderr_queue.put(line)

    def _thread_check_alive(self):

        """This Thread checks if retroarch is alive"""

        self.logger.debug('Starting Check Alive Thread')
        while 1:
            try:
                self._process.stdin.write('checkalive\n')
                self._running = True
            except:
                self._running = False
            time.sleep(0.1)

    def start(self, rom_path, core_path):

        """Start a Game ROM
        This Function needs the Path of the Plugin that could be used
        rom_path: Path to the Game ROM
        plugin_path: Path to the suitable Plugin from libretro
        Returns: True if everything was fine
        Returns: False an Error occured
        """

        self.logger.info('Send: Start ROM')
        rom_path = os.path.expanduser(rom_path)

        if not os.path.isfile(rom_path):
            self.logger.error('Error: Cant Start, Romfile not exist')
            self.logger.error(rom_path)
            return False

        if not os.path.isfile(core_path):
            self.logger.error('Error: Cant Start, Corefile not exist')
            self.logger.error(core_path)
            return False

        if self._running:
            self.logger.warning('Error: Cant Start, Rom already running')
            return False

        self.rom_path = rom_path
        self._running = True

        self.logger.info('Starting Rom: %s' % rom_path)
        self.logger.info('With Core: %s' % core_path)

        cmd = [self.pathes['retroarch_path'],
               '--config', self.pathes['configfile'],
               '--libretro', core_path, rom_path,
               '--size', self.settings['resolution'], '--verbose']

        if self.settings['fullscreen']:
            cmd.append('--fullscreen')

        self.logger.debug(str(cmd))

        self._process = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)

        rth = threading.Thread(target=self._thread_stderr_read)
        rth.daemon = True
        rth.start()

        time.sleep(0.5)

        if self._running:
            self.logger.info('Done')
            return True
        else:
            self.logger.error('Could not start')
            return False

    def stop(self):

        """Exit a running ROM"""

        if not self._running:
            self.logger.error('Rom is not running')
            return False

        self.logger.info('Send: Quit')

        if self._pause:
            self.toggle_pause()
            time.sleep(0.2)

        self._process.stdin.write('QUIT\n')
        while self._running:
            time.sleep(0.1)

        self.logger.info('Rom Exited Successfull')

    def toggle_pause(self):

        """Toggle from Pause to Unpause mode
        Returns: The new State: "Pause" or "Unpause" Mode
        Returns: False an Error occured
        """

        if not self._running:
            self.logger.error('Rom is not running')
            return False

        self._clear_stderr_queue()

        self.logger.info('Send: Toggle Pause')
        self._process.stdin.write('PAUSE_TOGGLE\n')
        time.sleep(0.1)

        answer = self._stderr_queue.get()
        if 'Paused.' in answer:
            self.logger.info('Paused')
            self._pause = True
            return 'paused'

        elif 'Unpaused.' in answer:
            self.logger.info('Unpaused')
            self._pause = False
            return 'unpaused'

        else:
            self.logger.warning(answer)
            self._pause = False
            return False

    def toggle_fullscreen(self):

        """Toggle from Window to Fullscreen mode
        Returns: The new State: "Fullscreen" or "Window" Mode
        Returns: False an Error occured
        """

        if not self._running:
            self.logger.error('Rom is not running')
            return False

        self._clear_stderr_queue()
        self.logger.info('Send: Fullscreen Toggle')
        self._process.stdin.write('FULLSCREEN_TOGGLE\n')
        time.sleep(0.5)
        found = False
        for _ in xrange(len(self._stderr_queue.queue)):
            answer = self._stderr_queue.get()
            if 'Video @' in answer:
                found = True
                break

        if not found:
            self.logger.error('Error in Fullscreen Toggle Answer')
            return False

        if 'Video @ fullscreen' in answer:
            self._fullscreen = True
            self.logger.info('Fullscreen Mode')
            return 'fullscreen'
        else:
            self._fullscreen = False
            self.logger.info('Window Mode')
            return 'window'

    def load(self, state):

        """Load a Savestate
        state: Raw State Data from save function
        """

        if not self._running:
            self.logger.error('Rom is not running')
            return False

        savepath = os.path.splitext(self.rom_path)[0]
        savepath = '%s.state' % savepath
        t_file = open(savepath, 'wb')
        t_file.write(state)
        t_file.close()

        # Savestate not possible in Pause Mode?
        toggle_pause = False
        if toggle_pause:
            self.toggle_pause()

        self.logger.info('Send: Load State')

        if self._pause:
            toggle_pause = True
            self.toggle_pause()

        self._process.stdin.write('LOAD_STATE\n')

        self._stderr_queue.get()
        self._stderr_queue.get()
        answer = self._stderr_queue.get()

        if 'Failed to load state' in answer:
            self.logger.info('Error: Load State Failed')
            return False
        elif 'Loaded state from slot' in answer:
            self.logger.info('Done: Loaded State')
            return True

    def _clear_stderr_queue(self):

        """Clear the Queue that holds the
         stderr Informations from retroarch"""

        while len(self._stderr_queue.queue) > 0:
            self._stderr_queue.get()

    def save(self):

        """Saves the State of the current Rom
        and returns the RAW Game Data.
        Return None: An Error occured
        """

        if not self._running:
            self.logger.error('Rom is not running')
            return False

        self._clear_stderr_queue()

        self.logger.info('Send: Save State')
        time.sleep(0.2)

        # Savestate not possible in Pause Mode?
        toggle_pause = False
        if self._pause:
            toggle_pause = True
            self.toggle_pause()

        self._process.stdin.write('SAVE_STATE\n')
        time.sleep(0.1)

        # Recieve Infos
        answer = self._stderr_queue.get()
        try:
            save_path = answer.split('"')[1]
        except:
            self.logger.error('Didnt recieve correct Infos from Stderr')
            self.logger.error('Got: %s' % answer)
            # Restore Pause Mode
            if toggle_pause:
                self.toggle_pause()
            return False
        self._stderr_queue.get()
        answer = self._stderr_queue.get()

        if 'Saved state to slot' not in answer:
            self.logger.error('Saving State Failed')
            # Restore Pause Mode
            if toggle_pause:
                self.toggle_pause()
            return False

        s_file = open(save_path, 'rb')
        data = s_file.read()
        s_file.close()
        os.remove(save_path)
        self.logger.info('Saved')
        # Restore Pause Mode
        if toggle_pause:
            self.toggle_pause()
        return data

    def reset(self):

        """Reset a running Rom and start from beginning"""

        if not self._running:
            self.logger.error('Rom is not running')
            return False

        time.sleep(0.3)
        self._clear_stderr_queue()

        self.logger.info('Send: Reset')

        if self._pause:
            self.toggle_pause()

        self._process.stdin.write('RESET\n')

        answer = self._stderr_queue.get()
        if 'Resetting game' in answer:
            self.logger.info('Reset')
            return True
        else:
            self.logger.error('Reset Failure')
            return False

    def _create_configfile(self):

        """Create the RetroArch Configfile"""

        if os.path.exists(self.pathes['configfile']):
            self.logger.info('Configfile exists already: %s'
                             % self.pathes['configfile'])
            self.logger.info('Dont overwrite!')
            return

        configfile = """
        stdin_cmd_enable = "true"

        # Configuration
        system_directory = "%s"
        config_save_on_exit = false

        # Controllers
        joypad_autoconfig_dir = "%s"
        input_autodetect_enable = true

        # Toggles eject for disks. Used for multiple-disk games.
        # input_disk_eject_toggle =

        # Cycles through disk images. Use after ejecting.
        # Complete by toggling eject again.
        # input_disk_next =
        """ % (self.pathes['bios'], self.pathes['controller'])

        self.logger.debug('Write Configfile:%s' % configfile)

        while '\n ' in configfile:
            configfile = configfile.replace('\n ', '\n')

        f_handle = open(self.pathes['configfile'], 'w')
        f_handle.write(configfile)
        f_handle.close()
