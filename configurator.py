import argparse
import logging
from preferences_editor import PreferencesEditor
import sys

DEBUG = "debug"
DETECTION_RATE = "detectionrate" #ms
LASER_INTENSITY = "laserintensity"
MARKER_RADIUS = "markerradius"
IGNORE_LASER_COLOR = "ignorelasercolor"
USE_VIRTUAL_MAGAZINE = "usevirtualmagazine"
VIRTUAL_MAGAZINE = "virtualmagazine"
USE_MALFUNCTIONS = "usemalfunctions"
MALFUNCTION_PROBABILITY = "malfunctionprobability"
VIDCAM = "vidcam" # first detected == 0

class Configurator():
    def _check_rate(self, rate):
        value = int(rate)
        if value < 1:
            raise argparse.ArgumentTypeError("DETECTION_RATE must be a number " +
                "greater than 0")
        return value  

    def _check_intensity(self, intensity):
        value = int(intensity)
        if value < 1 or value > 255:
            raise argparse.ArgumentTypeError("LASER_INTENSITY must be a number " +
                "between 1 and 255")
        return value   

    def _check_radius(self, radius):
        value = int(radius)
        if value < 1 or value > 20:
            raise argparse.ArgumentTypeError("MARKER_RADIUS must be a number " +
                "between 1 and 20")
        return value  
        
    def _check_vidcam(self, vidcam):
        value = int(vidcam)
        if value < 0 or value > 2:
            raise argparse.ArgumentTypeError("VIDCAM must be a number " +
                "between 0 and 2")
        return value

    def _check_ignore_laser_color(self, ignore_laser_color):
        ignore_laser_color = ignore_laser_color.lower()
        if ignore_laser_color != "red" and ignore_laser_color != "green":
            raise argparse.ArgumentTypeError("IGNORE_LASER_COLOR must be a string " +
                "equal to either \"green\" or \"red\" without quotes")
        return ignore_laser_color  

    def _check_virtual_magazine(self, virtual_magazine):
        value = int(virtual_magazine)
        if value < 1 or value > 45:
            raise argparse.ArgumentTypeError("VIRTUAL_MAGAZINE must be a number " +
                "between 1 and 45")
        return value

    def _check_malfunctions(self, malfunctions):
        value = float(malfunctions)
        if value < .1 or value > 99.9:
            raise argparse.ArgumentTypeError("MALFUNCTIONS_PROBABILITY must be a number " +
                "between .1 and 99.9")
        return value

    def __init__(self):
        self._logger = None

        # Load configuration information from the config file, which will
        # be over-ridden if settings are set on the command line
        config, preferences = PreferencesEditor.map_configuration()

        # Parse command line arguments
        parser = argparse.ArgumentParser(prog="shootoff.py")
        parser.add_argument("-d", "--debug", action="store_true", 
            help="turn on debug log messages")
        parser.add_argument("-r", "--detection-rate", type=self._check_rate,
            help="sets the rate at which shots are detected in milliseconds. " +
                "this should be set to about the length of time your laser trainer " +
                "stays on for each shot, typically about 100 ms")
        parser.add_argument("-i", "--laser-intensity", type=self._check_intensity, 
            help="sets the intensity threshold for detecting the laser [1,255]. " +
                "this should be as high as you can set it while still detecting " +
                "shots")
        parser.add_argument("-m", "--marker-radius", type=self._check_radius,
            help="sets the radius of shot markers in pixels [1,20]")
        parser.add_argument("-v", "--vidcam", type=self._check_vidcam,
            help="sets video camera to use [0,2]")
        parser.add_argument("-c", "--ignore-laser-color",
            type=self._check_ignore_laser_color,
            help="sets the color of laser that should be ignored by ShootOFF (green " +
                "or red). No color is ignored by default")
        parser.add_argument("-u", "--use-virtual-magazine",
            type=self._check_virtual_magazine,
            help="turns on the virtual magazine and sets the number rounds it holds")
        parser.add_argument("-f", "--use-malfunctions",
            type=self._check_malfunctions,
            help="turns on malfunctions and sets the probability of them happening")
	
        args = parser.parse_args()

        preferences[DEBUG] = args.debug

        if args.detection_rate:
            preferences[DETECTION_RATE] = int(args.detection_rate)

        if args.laser_intensity:
            preferences[LASER_INTENSITY] = int(args.laser_intensity)

        if args.marker_radius:
            preferences[MARKER_RADIUS] = int(args.marker_radius)
            
        if args.vidcam >= 0:
            preferences[VIDCAM] = int(args.vidcam)

        if args.ignore_laser_color:
            preferences[IGNORE_LASER_COLOR] = args.ignore_laser_color

        if args.use_virtual_magazine:
            preferences[USE_VIRTUAL_MAGAZINE] = True
            preferences[VIRTUAL_MAGAZINE] = int(args.use_virtual_magazine)

        if args.use_malfunctions:
            preferences[USE_MALFUNCTIONS] = True
            preferences[MALFUNCTION_PROBABILITY] = float(args.use_malfunctions)

        self._preferences = preferences
        self._config_parser = config

    def get_preferences(self):
        return self._preferences

    def get_config_parser(self):
        return self._config_parser

    def get_logger(self):
        if self._logger is None:
            self._logger = self._make_logger()

        return self._logger

    def _make_logger(self):
        logger = logging.getLogger('shootoff')
        stdhandler = logging.StreamHandler(sys.stdout)

        if self._preferences[DEBUG]:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        stdhandler.setFormatter(formatter)
        logger.addHandler(stdhandler)

        return logger
