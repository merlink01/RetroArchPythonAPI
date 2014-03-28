import os
import sys
import time
import Queue
import subprocess
import threading

__version__ = 0.01

class RetroArchPythonApi:

    """Retroarch Python API
    This is a Python API for the wonderfull RetroArch / libretro Libraries for Console Emulators
    Usage:
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
    """

    def __init__(self, retroarch_path, settings_path, bios_path, controller_path, resolution='800x600', start_fullscreen=True, debug=1):

        #Save Infos
        self.start_fullscreen = start_fullscreen
        self.debug = debug
        self.stderr_queue = Queue.Queue()
        self.pause = False
        self.resolution = resolution


        #Check RetroArch Path
        retroarch_path = os.path.abspath(retroarch_path)
        if os.path.isfile(retroarch_path):
            self.path_retroarch = retroarch_path
        else:
            sys.stderr.write('RetroArch Path not Found: %s\n Exiting.'%retroarch_path)
            sys.exit(1)

        #Pathes
        self.settings_path = os.path.abspath(settings_path)
        if not os.path.isdir(settings_path):
            os.makedirs(settings_path)

        self.bios_path = os.path.abspath(bios_path)
        if not os.path.isdir(self.bios_path):
            os.makedirs(self.bios_path)

        self.controller_path = os.path.abspath(controller_path)
        if not os.path.isdir(self.controller_path):
            os.makedirs(self.controller_path)

        #Settingsfile
        self.path_configfile = os.path.join(self.settings_path,'retroarch.cfg')

        #Start Check Alive Thread
        th = threading.Thread(target=self._thread_check_alive)
        th.daemon = True
        th.start()
        if self.debug:
            sys.stdout.write('Starting Retroarch Python API (Version:%s)\n'%__version__)
            sys.stdout.write('Start in Fullscreen: %s\n'%start_fullscreen)
            sys.stdout.write('Resolution: %s\n\n'%resolution)
            sys.stdout.write('Pathes:\n')
            sys.stdout.write('RetroArch Path:\t\t %s\n'%retroarch_path)
            sys.stdout.write('Settings Path:\t\t %s\n'%self.settings_path)
            sys.stdout.write('Bios Path:\t\t %s\n'%self.bios_path)
            sys.stdout.write('Gamecontroller Path:\t %s\n\n'%self.controller_path)


        #Create the Configfile
        self._create_configfile()
        if self.debug:
            sys.stdout.write('#'*30 + '\n\n')
            sys.stdout.flush()

    def _debug(self,message):
        if self.debug:
            if self.debug > 1:
                sys.stdout.write('\n%s\n'%('#'*30))
            sys.stdout.write('%s\n'%message)
            if self.debug > 1:
                sys.stdout.write('\n%s\n\n'%('#'*30))
            sys.stdout.flush()

    def _thread_stderr_read(self):
        while 1:
            try:
                line = self.process.stderr.readline().rstrip()

                if self.debug > 1:
                    print line

                if 'checkalive' in line:
                    continue
            except:
                self.running = False
                stderr_queue.put('error')
                break
            self.stderr_queue.put(line)

    def _thread_check_alive(self):
        """This Thread checks if retroarch is alive"""

        while 1:
            try:
                self.process.stdin.write('checkalive\n')
                self.running = True
            except:
                self.running = False
            time.sleep(.1)

    def is_running(self):
        """Check if a ROM is Running at the Moment
        Returns: True or False
        """
        return self.running

    def start(self,rom_path,plugin_path):
        """Start a Game ROM
        This Function needs the Path of the Plugin that could be used
        rom_path: Path to the Game ROM
        plugin_path: Path to the suitable Plugin from libretro
        Returns: True if everything was fine
        Returns: False an Error occured
        """

        self._debug('+Send: Start ROM')

        if self.running:
            self._debug('#Error: Cant Start, Rom already running')
            return False

        self.rom_path = rom_path
        self.running = True


        self._debug('+Starting Rom: %s'%rom_path)
        self._debug('+With Plugin: %s'%plugin_path)

        cmd = [self.path_retroarch,'--config',self.path_configfile,\
        '--libretro',plugin_path, rom_path,'--size',self.resolution,\
        '--verbose']

        if self.start_fullscreen:
            cmd.append('--fullscreen')

        self.process = subprocess.Popen(cmd, stdin=subprocess.PIPE,\
                                             stderr=subprocess.PIPE,\
                                             stdout=subprocess.PIPE)
        th = threading.Thread(target=self._thread_stderr_read)
        th.daemon = True
        th.start()
        time.sleep(0.5)

        if self.running:
            self._debug('#Done: Starting')
            return True
        else:
            self._debug('#Error: Could not start')
            return False


    def quit(self):
        """Exit a running ROM"""

        self._debug('+Send: Quit')

        if self.pause:
            self.toggle_pause()
            time.sleep(.2)

        self.process.stdin.write('QUIT\n')
        while self.running:
            time.sleep(0.1)

        self._debug('#Done: Rom Exited Successfull')


    def toggle_pause(self):
        """Toggle from Pause to Unpause mode
        Returns: The new State: "Pause" or "Unpause" Mode
        Returns: False an Error occured"""

        self._clear_stderr_queue()

        self._debug('+Send: Toggle Pause')
        self.process.stdin.write('PAUSE_TOGGLE\n')
        time.sleep(0.1)

        answer = self.stderr_queue.get()
        if 'Paused.' in answer:
            self._debug('#Done: Paused')
            self.pause = True
            return 'Pause'

        elif 'Unpaused.' in answer:
            self._debug('#Done: Unpaused')
            self.pause = False
            return 'Unpause'

        else:
            self._debug(answer)
            self.pause = False
            return False



    def toggle_fullscreen(self):
        """Toggle from Window to Fullscreen mode
        Returns: The new State: "Fullscreen" or "Window" Mode
        Returns: False an Error occured"""

        self._clear_stderr_queue()
        self._debug('+Send: Fullscreen Toggle')
        self.process.stdin.write('FULLSCREEN_TOGGLE\n')
        time.sleep(0.5)
        found = False
        for entry in xrange(len(self.stderr_queue.queue)):
            answer = self.stderr_queue.get()
            if 'Video @' in answer:
                found = True
                break

        if not found:
            self._debug('#Error: Fullscreen Toggle Answer')
            return False

        if 'Video @ fullscreen' in answer:
            self.fullscreen = True
            self._debug('#Done: Fullscreen Mode')
            return 'Fullscreen'
        else:
            self.fullscreen = False
            self._debug('#Done: Window Mode')
            return 'Window'





    def load(self,state):
        """Load a Savestate
        state: Raw State Data from save function
        """

        savepath = os.path.splitext(self.rom_path)[0]
        savepath = '%s.state'%savepath
        t_file = open(savepath,'wb')
        t_file.write(state)
        t_file.close()

        #Savestate not possible in Pause Mode?
        toggle_pause = False
        if toggle_pause:
            self.toggle_pause()

        self._debug('+Send: Load State')

        if self.pause:
            toggle_pause = True
            self.toggle_pause()

        self.process.stdin.write('LOAD_STATE\n')

        self.stderr_queue.get()
        self.stderr_queue.get()
        answer = self.stderr_queue.get()

        if  'Failed to load state' in answer:
            self._debug('#Error: Load State Failed')
            return False
        elif 'Loaded state from slot' in answer:
            self._debug('#Done: Loaded State')
            return True


    def _clear_stderr_queue(self):
        while len(self.stderr_queue.queue) > 0:
            self.stderr_queue.get()

    def save(self):

        """Saves the State of the current Rom
        and returns the RAW Game Data.
        Return None: An Error occured
        """

        self._clear_stderr_queue()

        self._debug('+Send: Save State')
        time.sleep(0.2)

        #Savestate not possible in Pause Mode?
        toggle_pause = False
        if self.pause:
            toggle_pause = True
            self.toggle_pause()

        self.process.stdin.write('SAVE_STATE\n')
        time.sleep(0.1)

        #Recieve Infos
        answer = self.stderr_queue.get()
        try:
            save_path = answer.split('"')[1]
        except:
            self._debug('#Error: Didnt recieve correct Infos from Stderr')
            self._debug('#Error: Got: %s'%answer)
            #Restore Pause Mode
            if toggle_pause:
                self.toggle_pause()
            return False
        self.stderr_queue.get()
        answer = self.stderr_queue.get()

        if not 'Saved state to slot' in answer:
            self._debug('#Error: Saving State Failed')
            #Restore Pause Mode
            if toggle_pause:
                self.toggle_pause()
            return False

        s_file = open(save_path,'rb')
        data = s_file.read()
        s_file.close()
        os.remove(save_path)
        self._debug('#Done: Saved')
        #Restore Pause Mode
        if toggle_pause:
            self.toggle_pause()
        return data


    def reset(self):
        """Reset a running Rom and start from beginning"""

        time.sleep(0.3)
        self._clear_stderr_queue()

        self._debug('+Send: Reset')

        if self.pause:
            self.toggle_pause()

        self.process.stdin.write('RESET\n')

        answer = self.stderr_queue.get()
        if 'Resetting game' in answer:
            self._debug('#Done: Reset')
            return True
        else:
            self._debug('#Error: Reset Failure')
            return False

    def _create_configfile(self):
        if os.path.exists(self.path_configfile):
            self._debug('Configfile exists already: %s'%self.path_configfile)
            self._debug('Dont overwrite!')
            return

        configfile = """
        config_save_on_exit = false

        stdin_cmd_enable = "true"

        system_directory = "%s"
        input_autodetect_enable = true
        joypad_autoconfig_dir = "%s"

        # Toggles eject for disks. Used for multiple-disk games.
        # input_disk_eject_toggle =

        # Cycles through disk images. Use after ejecting.
        # Complete by toggling eject again.
        # input_disk_next =
        """%(self.bios_path,self.controller_path)

        LOG.debug('Write Configfile:\n%s'%configfile)

        while '\n ' in configfile:
             configfile = configfile.replace('\n ','\n')

        f_handle = open(self.path_configfile,'w')
        f_handle.write(configfile)
        f_handle.close()

