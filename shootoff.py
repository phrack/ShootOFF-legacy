#!/usr/bin/env python2

# Copyright (c) 2013 phrack. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import argparse
from canvas_manager import CanvasManager
import cv2
import glob
import imp
import logging
import os
from PIL import Image, ImageTk
from preferences_editor import PreferencesEditor
from shot import Shot
from tag_parser import TagParser
from target_editor import TargetEditor
from target_pickler import TargetPickler
from training_protocols.protocol_operations import ProtocolOperations
import sys
from threading import Thread
import Tkinter, tkMessageBox

FEED_FPS = 30 #ms
DETECTION_RATE = "detectionrate" #ms
LASER_INTENSITY = "laserintensity"
MARKER_RADIUS = "markerradius"
TARGET_VISIBILTY_MENU_INDEX = 3

class MainWindow:
    def refresh_frame(self, *args):
        rval, self._webcam_frame = self._cv.read()

        if (rval == False):
            logger.critical("The webcam has been disconnected.")
            self._shutdown = True
            return

        for shot in self._shots:
            shot.draw_marker(self._webcam_frame)  

        webcam_image = self._webcam_frame

        # If the shot detector saw interference, we need to show it now
        if self._show_interference:
            if self._interference_iterations > 0:
                self._interference_iterations -= 1

                frame_bw = cv2.cvtColor(self._webcam_frame, cv2.cv.CV_BGR2GRAY)
                (thresh, webcam_image) = cv2.threshold(frame_bw,
                    self._preferences[LASER_INTENSITY], 255,
                    cv2.THRESH_BINARY)             

        # Show webcam image a Tk image container (note:
        # if the image isn't stored in an instance variable
        # it will be garbage collected and not show)
        self._image = ImageTk.PhotoImage(image=Image.fromarray(webcam_image))

        # If the target editor doesn't have its own copy of the image
        # the webcam feed will never update again after the editor opens
        self._editor_image = ImageTk.PhotoImage(
            image=Image.fromarray(webcam_image))

        webcam_image = self._webcam_canvas.create_image(0, 0, image=self._image,
            anchor=Tkinter.NW, tags=("background"))

        # Drawing the new frame covers up our targets, so
        # move it to the back if they are supposed to show
        if self._show_targets:
            # Not raising existing targets while lowering the webcam feed
            # will cause hits to stop registering on targets
            for target in self._targets:
                self._webcam_canvas.tag_raise(target)
            self._webcam_canvas.tag_lower(webcam_image)
        else:
            # We have to lower canvas then the targets so 
            # that anything drawn by plugins will still show
            # but the targets won't
            self._webcam_canvas.tag_lower(webcam_image)        
            for target in self._targets:
                self._webcam_canvas.tag_lower(target)

        if self._shutdown == False:
            self._window.after(FEED_FPS, self.refresh_frame)

    def detect_shots(self):
        if (self._webcam_frame is None):
            self._window.after(self._preferences[DETECTION_RATE], self.detect_shots)
            return

        # Makes feed black and white
        frame_bw = cv2.cvtColor(self._webcam_frame, cv2.cv.CV_BGR2GRAY)

        # Threshold the image
        (thresh, frame_thresh) = cv2.threshold(frame_bw, 
            self._preferences[LASER_INTENSITY], 255, cv2.THRESH_BINARY)
	
        # Determine if we have a light source or glare on the feed
        if not self._seen_interference:
            self.detect_interfence(frame_thresh)     

        # Find min and max values on the black and white frame
        min_max = cv2.minMaxLoc(frame_thresh)

        # The minimum and maximum are the same if there was
        # nothing detected
        if (min_max[0] != min_max[1]):
            x = min_max[3][0]
            y = min_max[3][1]

            new_shot = Shot((x, y), self._preferences[MARKER_RADIUS])
            self._shots.append(new_shot)

            # Process the shot to see if we hit a region and perform
            # a training protocol specific action and any if we did
            # command tag actions if we did
            self.process_hit(new_shot)

        if self._shutdown == False:
            self._window.after(self._preferences[DETECTION_RATE], self.detect_shots)

    def detect_interfence(self, image_thresh):
        brightness_hist = cv2.calcHist([image_thresh],[0],None,[256],[0,255])
        percent_dark =  brightness_hist[0] / image_thresh.size

        # If 99% of thresholded image isn't dark, we probably have
        # a light source or glare in the image
        if (percent_dark < .99):
            # We will only warn about interference once each run
            self._seen_interference = True

            logging.warning(
                "Glare or light source detected. %f of the image is dark." %
                percent_dark)

            self._show_interference = tkMessageBox.askyesno("Interference Detected", "Bright glare or a light source has been detected on the webcam feed, which will interfere with shot detection. Do you want to see a feed where the interference will be white and everything else will be black for a short period of time?") 

            if self._show_interference:
                # calculate the number of times we should show the 
                # interference image (this should be roughly 5 seconds)
                self._interference_iterations = 2500 / FEED_FPS    

    def process_hit(self, shot):
        is_hit = False

        x = shot.get_coords()[0]
        y = shot.get_coords()[1]

        regions = self._webcam_canvas.find_overlapping(x, y, x, y)

        # If we hit a targert region, run its commands and notify the
        # loaded plugin of the hit
        for region in reversed(regions):
            tags = TagParser.parse_tags(
                self._webcam_canvas.gettags(region))

            if "_internal_name" in tags and "command" in tags:
                self.execute_region_commands(tags["command"])

            if "_internal_name" in tags and self._loaded_training != None:
                self._loaded_training.hit_listener(region, tags)

            if "_internal_name" in tags:
                is_hit = True
                # only run the commands and notify a hit for the top most
                # region
                break

        if self._loaded_training != None: 
            self._loaded_training.shot_listener(shot, is_hit)

    def open_target_editor(self):
        TargetEditor(self._frame, self._editor_image, 
            notifynewfunc=self.new_target_listener)

    def add_target(self, name):
        target_name = "_internal_name:target" + str(len(self._targets))

        target_pickler = TargetPickler()
        (region_object, regions) = target_pickler.load(
            name, self._webcam_canvas, target_name)

        self._targets.append(target_name)

    def edit_target(self, name):
        TargetEditor(self._frame, self._editor_image, name,
            self.new_target_listener)

    def new_target_listener(self, target_file):
        (root, ext) = os.path.splitext(os.path.basename(target_file))
        self._add_target_menu.add_command(label=root, 
                command=self.callback_factory(self.add_target,
                target_file))
        self._edit_target_menu.add_command(label=root, 
                command=self.callback_factory(self.edit_target,
                target_file))

    def execute_region_commands(self, command_list):
        for command in command_list:
            if command == "clear_shots":
                self.clear_shots()

    def toggle_target_visibility(self):
        if self._show_targets:
            self._targets_menu.entryconfig(TARGET_VISIBILTY_MENU_INDEX,
                label="Show Targets")
        else:
            self._targets_menu.entryconfig(TARGET_VISIBILTY_MENU_INDEX,
                label="Hide Targets")

        self._show_targets = not self._show_targets

    def clear_shots(self):
        self._shots = []
        if self._loaded_training != None:
            self._loaded_training.reset()

    def quit(self):
        self._shutdown = True
        self._window.quit()

    def canvas_click(self, event):
        # find the target that was selected
        # if a target wasn't clicked, _selected_target
        # will be empty and all targets will be dim
        selected_region = event.widget.find_closest(
            event.x, event.y)
        target_name = ""

        for tag in self._webcam_canvas.gettags(selected_region):
            if tag.startswith("_internal_name:"): 
                target_name = tag
                break
        
        if self._selected_target == target_name:
            return

        self._canvas_manager.selection_update_listener(self._selected_target,
            target_name)
        self._selected_target = target_name

    def canvas_delete_target(self, event):
        if (self._selected_target):
            for target in self._targets:
                if target == self._selected_target:
                    self._targets.remove(target)
            event.widget.delete(self._selected_target)
            self._selected_target = ""

    def cancel_training(self):
        if self._loaded_training is not None:
            self._loaded_training.destroy()
            self._loaded_training = None
    
    def load_training(self, plugin):
        # Create a list of targets, their regions, and the tags attached
        # to those regions so that the plugin can have a stock of what
        # can be shot
        targets = [] 

        for target in self._targets:
            target_regions = self._webcam_canvas.find_withtag(target)
            target_data = {"name":target, "regions":[]}
            targets.append(target_data)

            for region in target_regions:
                tags = TagParser.parse_tags(
                    self._webcam_canvas.gettags(region))
                target_data["regions"].append(tags)

        if self._loaded_training:
            self._loaded_training.destroy()
            self._protocol_operations.destroy()
    
        self._protocol_operations = ProtocolOperations(self._webcam_canvas)
        self._loaded_training = imp.load_module("__init__", *plugin).load(
            self._protocol_operations, targets)       

    def edit_preferences(self):
        preferences_editor = PreferencesEditor(self._window, self._config,
            self._preferences)

    def build_gui(self, feed_dimensions=(600,600)):
        # Create the main window
        self._window = Tkinter.Tk()
        self._window.protocol("WM_DELETE_WINDOW", self.quit)
        self._window.title("ShootOFF")

        self._frame = Tkinter.Frame(self._window)
        self._frame.pack(padx=15, pady=15)    

        # Create the container for our webcam image
        self._webcam_canvas = Tkinter.Canvas(self._frame, 
            width=feed_dimensions[0], height=feed_dimensions[1])      
        self._webcam_canvas.pack()

        self._webcam_canvas.bind('<ButtonPress-1>', self.canvas_click)
        self._webcam_canvas.bind('<Delete>', self.canvas_delete_target)

        self._canvas_manager = CanvasManager(self._webcam_canvas)
    
        # Create a button to clear shots
        self._clear_shots_button = Tkinter.Button(
            self._frame, text="Clear Shots", command=self.clear_shots)
        self._clear_shots_button.pack()

        self.create_menu()

    def create_menu(self):
        menu_bar = Tkinter.Menu(self._window)
        self._window.config(menu=menu_bar)
    
        file_menu = Tkinter.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="Preferences", command=self.edit_preferences)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

        # Update TOGGLE_VISIBILTY_INDEX if another command is added
        # before the high targets command
        self._targets_menu = Tkinter.Menu(menu_bar, tearoff=False)
        self._targets_menu.add_command(label="Create Target...", 
            command=self.open_target_editor)
        self._add_target_menu = self.create_target_list_menu(
            self._targets_menu, "Add Target", self.add_target)
        self._edit_target_menu = self.create_target_list_menu(
            self._targets_menu, "Edit Target", self.edit_target)
        self._targets_menu.add_command(label="Hide Targets",
            command=self.toggle_target_visibility)
        menu_bar.add_cascade(label="Targets", menu=self._targets_menu)

        training_menu = Tkinter.Menu(menu_bar, tearoff=False)

        # Add none button to turn off training protocol
        self._training_selection = Tkinter.StringVar()
        name = "None"
        training_menu.add_radiobutton(label=name, command=self.cancel_training,
                variable=self._training_selection, value=name)
        self._training_selection.set(name)

        self.create_training_list(training_menu, self.load_training)   
        menu_bar.add_cascade(label="Training", menu=training_menu)     

    def callback_factory(self, func, name):
        return lambda: func(name)

    def create_target_list_menu(self, menu, name, func):
        targets = glob.glob("targets/*.target")     

        target_list_menu = Tkinter.Menu(menu, tearoff=False)

        for target in targets:
            (root, ext) = os.path.splitext(os.path.basename(target)) 
            target_list_menu.add_command(label=root, 
                command=self.callback_factory(func, target))

        menu.add_cascade(label=name, menu=target_list_menu)

        return target_list_menu

    def create_training_list(self, menu, func):
        protocols_dir = "training_protocols"

        plugin_candidates = os.listdir(protocols_dir)
        for candidate in plugin_candidates:
            plugin_location = os.path.join(protocols_dir, candidate)
            if (not os.path.isdir(plugin_location) or 
                not "__init__.py" in os.listdir(plugin_location)):
                continue
            plugin_info = imp.find_module("__init__", [plugin_location])
            training_info = imp.load_module("__init__", *plugin_info).get_info()
            menu.add_radiobutton(label=training_info["name"], 
                command=self.callback_factory(self.load_training, plugin_info),
                variable=self._training_selection, value=training_info["name"])

    def __init__(self, config, preferences):
        self._shots = []
        self._targets = []
        self._show_targets = True
        self._selected_target = ""
        self._loaded_training = None
        self._seen_interference = False
        self._show_interference = False
        self._webcam_frame = None
        self._config = config
        self._preferences = preferences

        self._cv = cv2.VideoCapture(0)

        if self._cv.isOpened():
            width = self._cv.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)
            height = self._cv.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)

            # If the resolution is too low, try to force it higher.
            # Some users have drivers that default to extremely low
            # resolutions and opencv doesn't currently make it easy
            # to enumerate valid resolutions and switch to them
            if width < 640 and height < 480:
                logger.info("Webcam resolution is current low (%dx%d), " + 
                    "attempting to increase it to 640x480", width, height)
                self._cv.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 640)
                self._cv.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 480)
                width = self._cv.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)
                height = self._cv.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)               

            logger.debug("Webcam resolution is %dx%d", width, height) 
            self.build_gui((width, height))

            fps = self._cv.get(cv2.cv.CV_CAP_PROP_FPS)
            if fps == -1:
                logger.info("Couldn't get webcam FPS, defaulting to 30.")
            else: 
                FEED_FPS = fps
                logger.info("Feed FPS set to %d.", fps)

            # Webcam related threads will end when this is true
            self._shutdown = False

            #Start the refresh loop that shows the webcam feed           
            self._refresh_thread = Thread(target=self.refresh_frame,
                name="refresh_thread")
            self._refresh_thread.start()

            #Start the shot detection loop
            self._shot_detection_thread = Thread(target=self.detect_shots,
                name="shot_detection_thread")
            self._shot_detection_thread.start()
        else:
            logger.critical("Video capturing could not be initialized either " +
                "because there is no webcam or we cannot connect to it.")
            self._shutdown = True

    def main(self):
        if not self._shutdown:
            Tkinter.mainloop()

def check_rate(rate):
    value = int(rate)
    if value < 1:
        raise argparse.ArgumentTypeError("DETECTION_RATE must be a number " +
            "greater than 0")
    return value  

def check_intensity(intensity):
    value = int(intensity)
    if value < 0 or value > 255:
        raise argparse.ArgumentTypeError("LASER_INTENSITY must be a number " +
            "between 0 and 255")
    return value   

def check_radius(radius):
    value = int(radius)
    if value < 1 or value > 20:
        raise argparse.ArgumentTypeError("MARKER_RADIUS must be a number " +
            "between 1 and 20")
    return value  

if __name__ == "__main__":
    # Load configuration information from the config file, which will
    # be over-ridden if settings are set on the command line
    config, preferences = PreferencesEditor.map_configuration()

    # Parse command line arguments
    parser = argparse.ArgumentParser(prog="shootoff.py")
    parser.add_argument("-d", "--debug", action="store_true", 
        help="turn on debug log messages")
    parser.add_argument("-r", "--detection-rate", type=check_rate,
        help="sets the rate at which shots are detected in milliseconds. " +
            "this should be set to about the length of time your laser trainer " +
            "stays on for each shot, typically about 100 ms")
    parser.add_argument("-i", "--laser-intensity", type=check_intensity, 
        help="sets the intensity threshold for detecting the laser [0,255]. " +
            "this should be as high as you can set it while still detecting " +
            "shots")
    parser.add_argument("-m", "--marker-radius", type=check_radius,
        help="sets the radius of shot markers in pixels [1,20]")
    args = parser.parse_args()

    if args.detection_rate:
        preferences[DETECTION_RATE] = args.detection_rate

    if args.laser_intensity:
        preferences[LASER_INTENSITY] = args.laser_intensity

    if args.marker_radius:
        preferences[MARKER_RADIUS] = args.marker_radius

    # Configure logging
    logger = logging.getLogger('shootoff')
    stdhandler = logging.StreamHandler(sys.stdout)
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stdhandler.setFormatter(formatter)
    logger.addHandler(stdhandler)

    # Start the main window
    mainWindow = MainWindow(config, preferences)
    mainWindow.main()
