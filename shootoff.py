#!/usr/bin/env python2

# Copyright (c) 2013 phrack. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from canvas_manager import CanvasManager
import configurator
from configurator import Configurator
import cv2
import glob
import imp
import numpy
import os
from PIL import Image, ImageTk
import platform
from preferences_editor import PreferencesEditor
from projector_arena import ProjectorArena
from projector_calibrator import ProjectorCalibrator
import random
from shot import Shot
from tag_parser import TagParser
from target_editor import TargetEditor
import time
from training_protocols.protocol_operations import ProtocolOperations
from threading import Thread
import Tkinter, tkFileDialog, tkMessageBox, ttk

FEED_FPS = 30  # ms
SHOT_MARKER = "shot_marker"
TARGET_VISIBILTY_MENU_INDEX = 3

PROJECTOR_ARENA_MENU_INDEX = 0
PROJECTOR_CALIBRATE_MENU_INDEX = 1
PROJECTOR_ADD_TARGET_MENU_INDEX = 2

DEFAULT_SHOT_LIST_COLUMNS = ("Time", "Laser")

class MainWindow:
    def refresh_frame(self, *args):
        rval, self._webcam_frame = self._cv.read()

        if (rval == False):
            self._refresh_miss_count += 1
            self._logger.debug ("Missed %d webcam frames. If we miss too many ShootOFF " +
                "will stop processing shots.", self._refresh_miss_count)

            if self._refresh_miss_count >= 25:
                tkMessageBox.showerror("Webcam Disconnected", "Missed too many " +
                    "webcam frames. The camera is probably disconnected so " +
                    "ShootOFF will stop processing shots.")
                self._logger.critical("Missed %d webcam frames. The camera is probably " +
                    "disconnected so ShootOFF will stop processing shots.",
                    self._refresh_miss_count)
                self._shutdown = True
            else:
                if self._shutdown == False:
                    self._window.after(FEED_FPS, self.refresh_frame)

            return

        self._refresh_miss_count = 0

        #OpenCV reads the frame in BGR, but PIL uses RGB, so we if we don't
        #convert it, the colors will be off.
        webcam_image = cv2.cvtColor(self._webcam_frame, cv2.cv.CV_BGR2RGB)

        if self._calibrate_projector:
            webcam_image = self._projector_calibrator.calibrate_projector(webcam_image)

        # If the shot detector saw interference, we need to show it now
        if self._show_interference:
            if self._interference_iterations > 0:
                self._interference_iterations -= 1

                frame_bw = cv2.cvtColor(self._webcam_frame, cv2.cv.CV_BGR2GRAY)
                (thresh, webcam_image) = cv2.threshold(frame_bw,
                    self._preferences[configurator.LASER_INTENSITY], 255,
                    cv2.THRESH_BINARY)

        # Show webcam image a Tk image container (note:
        # if the image isn't stored in an instance variable
        # it will be garbage collected and not show)
        self._image = ImageTk.PhotoImage(image=Image.fromarray(webcam_image))

        # If the target editor doesn't have its own copy of the image
        # the webcam feed will never update again after the editor opens
        self._editor_image = ImageTk.PhotoImage(
            image=Image.fromarray(webcam_image))

        self._webcam_canvas.delete("background")
        webcam_image = self._webcam_canvas.create_image(0, 0, image=self._image,
            anchor=Tkinter.NW, tags=("background"))

        # Drawing the new frame covers up our targets, so
        # move it to the back if they are supposed to show
        if self._show_targets:
            # Not raising existing targets while lowering the webcam feed
            # will cause hits to stop registering on targets
            for target in self._targets:
                self._webcam_canvas.tag_raise(target)
            self._webcam_canvas.tag_raise(SHOT_MARKER)
            self._webcam_canvas.tag_lower(webcam_image)
        else:
            # We have to lower canvas then the targets so
            # that anything drawn by plugins will still show
            # but the targets won't
            self._webcam_canvas.tag_raise(SHOT_MARKER)
            self._webcam_canvas.tag_lower(webcam_image)
            for target in self._targets:
                self._webcam_canvas.tag_lower(target)

        if self._shutdown == False:
            self._window.after(FEED_FPS, self.refresh_frame)

    def detect_shots(self):
        if (self._webcam_frame is None):
            self._window.after(self._preferences[configurator.DETECTION_RATE], self.detect_shots)
            return

        # Makes feed black and white
        frame_bw = cv2.cvtColor(self._webcam_frame, cv2.cv.CV_BGR2GRAY)

        # Threshold the image
        (thresh, frame_thresh) = cv2.threshold(frame_bw, 
            self._preferences[configurator.LASER_INTENSITY], 255, cv2.THRESH_BINARY)

        # Determine if we have a light source or glare on the feed
        if not self._seen_interference:
            self.detect_interfence(frame_thresh)

        # Detect shots by splitting the frame into 9 regions (3 horizontally, and
        # and 3 vertically -- picture a tic-tac-toe board) and detecting shots in
        # each region separately
        frame_height = len(frame_thresh)
        frame_width = len(frame_thresh[0])

        sub_height = frame_height / 3
        sub_width = frame_width / 3

        for sub_y in range(0, frame_height, sub_height):
            for sub_x in range(0, frame_width, sub_width):
                # Find min and max values on the black and white frame
                min_max = cv2.minMaxLoc(frame_thresh[sub_y:sub_y + sub_height,sub_x:sub_x + sub_width])
                            
                # The minimum and maximum are the same if there was
                # nothing detected
                if (min_max[0] != min_max[1]):
                    x = min_max[3][0] + sub_x
                    y = min_max[3][1] + sub_y

                    laser_color = self.detect_laser_color(x, y)

                    # If we couldn't detect a laser color, it's probably not a
                    # shot
                    if (laser_color is not None and
                        self._preferences[configurator.IGNORE_LASER_COLOR] not in laser_color):

                        self.handle_shot(laser_color, x, y)

        if self._shutdown == False:
            self._window.after(self._preferences[configurator.DETECTION_RATE],
                self.detect_shots)

    def handle_shot(self, laser_color, x, y):	
        if (self._pause_shot_detection):
            return 

        if self.update_virtual_magazine():
            return

        if self.malfunction():
            return

        timestamp = 0
        hit_projector_region = None
        projector_region_tags = None

        # If the projector is calibrated and the shot is in the
        # projector's bounding box, tell the projector arena
        if self._projector_calibrated:
            bbox = self._projector_calibrator.get_projected_bbox()
            x_scale = float(self._projector_arena.arena_width()) / float(bbox[2] - bbox[0])
            y_scale = float(self._projector_arena.arena_height()) / float(bbox[3] - bbox[1])
            if (x > bbox[0] and x < bbox[2] and y > bbox[1] and y < bbox[3]):
                # Translate the coordinates into the arena's coordinate system
                hit_projector_region, projector_region_tags = self._projector_arena.handle_shot(laser_color, 
                    (x - bbox[0])*x_scale, (y - bbox[1])*y_scale)
        # This makes sure click to shoot can be used for the projector too
        if self._preferences[configurator.DEBUG]:
            frame_height = len(self._webcam_frame)
            frame_width = len(self._webcam_frame[0])
            x_scale = float(self._projector_arena.arena_width()) / float(frame_width)
            y_scale = float(self._projector_arena.arena_height()) / float(frame_height)
            hit_projector_region, projector_region_tags = self._projector_arena.handle_shot(laser_color, 
                    (x)*x_scale, (y)*y_scale)
      
        # Start the shot timer if it has not been started yet,
        # otherwise get the time offset
        if self._shot_timer_start is None:
            self._shot_timer_start = time.time()
        else:
            timestamp = time.time() - self._shot_timer_start

        tree_item = None

        if "green" in laser_color:
            tree_item = self._shot_timer_tree.insert("", "end",
                values=[timestamp, "green"])
        else:
            tree_item = self._shot_timer_tree.insert("", "end",
                values=[timestamp, laser_color])
        self._shot_timer_tree.see(tree_item)

        new_shot = Shot((x, y), self._webcam_canvas,
            self._preferences[configurator.MARKER_RADIUS],
            laser_color, timestamp)
        self._shots.append(new_shot)
        new_shot.draw_marker()

        if hit_projector_region != None  and self._loaded_training != None:
            self._loaded_training.hit_listener(hit_projector_region, projector_region_tags, 
                new_shot, tree_item)
            return

        # Process the shot to see if we hit a region and perform
        # a training protocol specific action and any if we did
        # command tag actions if we did
        self.process_hit(new_shot, tree_item)

    def update_virtual_magazine(self):
        if self._preferences[configurator.USE_VIRTUAL_MAGAZINE]:
            if self._virtual_magazine_rounds == -1:
                self._virtual_magazine_rounds = self._preferences[configurator.VIRTUAL_MAGAZINE]

            if self._virtual_magazine_rounds == 0:
                self._protocol_operations.say("reload")
                self._virtual_magazine_rounds = self._preferences[configurator.VIRTUAL_MAGAZINE]

                return True
            else:
                self._virtual_magazine_rounds -= 1

        return False

    def malfunction(self):
        if self._preferences[configurator.USE_MALFUNCTIONS]:
            if random.random() < self._preferences[configurator.MALFUNCTION_PROBABILITY] / 100:
                self._protocol_operations.say("malfunction")
                
                return True

        return False

    def detect_interfence(self, image_thresh):
        brightness_hist = cv2.calcHist([image_thresh], [0], None, [256], [0, 255])
        percent_dark = brightness_hist[0] / image_thresh.size

        # If 99% of thresholded image isn't dark, we probably have
        # a light source or glare in the image
        if (percent_dark < .99):
            # We will only warn about interference once each run
            self._seen_interference = True

            self._logger.warning(
                "Glare or light source detected. %f of the image is dark." %
                percent_dark)

            self._show_interference = tkMessageBox.askyesno("Interference Detected", "Bright glare or a light source has been detected on the webcam feed, which will interfere with shot detection. Do you want to see a feed where the interference will be white and everything else will be black for a short period of time?")

            if self._show_interference:
                # calculate the number of times we should show the
                # interference image (this should be roughly 5 seconds)
                self._interference_iterations = 2500 / FEED_FPS

    def detect_laser_color(self, x, y):
        # Get the average color around the coordinates. If
        # the dominant color is red, it's a red laser, if
        # it's green it's a green laser, otherwise it's probably
        # not a laser trainer, so ignore it
        l = self._webcam_frame.shape[1]
        h = self._webcam_frame.shape[0]
        mask = numpy.zeros((h, l, 1), numpy.uint8)
        cv2.circle(mask, (x, y), 10, (255, 255, 555), -1)
        mean_color = cv2.mean(self._webcam_frame, mask)

        # Remember that self._webcam_frame is in BGR
        r = mean_color[2]
        g = mean_color[1]
        b = mean_color[0]

        # We only detect a color if the largest component is at least
        # 2% bigger than the other components. This is based on the
        # heuristic that noise tends to have color values that are very
        # similar
        if (g == 0 or b == 0): 
            return None

        if (r / g) > 1.02 and (r / b) > 1.02:
            return "red"

        if (r == 0 or b == 0): 
            return None

        if (g / r) > 1.02 and (g / b) > 1.02:
            return "green2"

        return None

    def process_hit(self, shot, shot_list_item):
        is_hit = False

        x = shot.get_coords()[0]
        y = shot.get_coords()[1]

        regions = self._webcam_canvas.find_overlapping(x, y, x, y)

        # If we hit a targert region, run its commands and notify the
        # loaded plugin of the hit
        for region in reversed(regions):
            tags = TagParser.parse_tags(self._webcam_canvas.gettags(region))

            # If we hit an image on a transparent pixel, ignore the "hit"
            if "_shape:image" in self._webcam_canvas.gettags(region) and self._canvas_manager.is_transparent_pixel(region, x, y):
                    continue

            if "_internal_name" in tags and "command" in tags:
                self._canvas_manager.execute_region_commands(region, tags["command"], self._protocol_operations)

            if "_internal_name" in tags and self._loaded_training != None:
                self._loaded_training.hit_listener(region, tags, shot, shot_list_item)

            if "_internal_name" in tags:
                is_hit = True
                # only run the commands and notify a hit for the top most
                # region
                break

        # Also run commands for all hidden regions that were hit
        for region in regions:
            tags = TagParser.parse_tags(self._webcam_canvas.gettags(region))

            if "visible" in tags and "command" in tags and tags["visible"].lower() == "false":                
                self._canvas_manager.execute_region_commands(region, tags["command"], self._protocol_operations)

        if self._loaded_training != None:
            self._loaded_training.shot_listener(shot, shot_list_item, is_hit)   

    def get_protocol_operations(self):
        return self._protocol_operations

    def open_target_editor(self):
        TargetEditor(self._frame, self._editor_image,
                     notifynewfunc=self.new_target_listener)

    def add_target(self, name):
        target_name = self._canvas_manager.add_target(name, self._image_regions_images)
        self._targets.append(target_name)

    def edit_target(self, name):
        TargetEditor(self._frame, self._editor_image, name,
                     self.new_target_listener)

    def new_target_listener(self, target_file, is_animated):
        (root, ext) = os.path.splitext(os.path.basename(target_file))

        if not is_animated:
            self._add_target_menu.add_command(label=root,
                    command=self.callback_factory(self.add_target,
                    target_file))
        else:
            self._add_projector_target_menu.add_command(label=root,
                    command=self.callback_factory(self._projector_arena.add_target,
                    target_file))

        self._edit_target_menu.add_command(label=root,
                command=self.callback_factory(self.edit_target,
                target_file))

    def toggle_target_visibility(self):
        if self._show_targets:
            self._targets_menu.entryconfig(TARGET_VISIBILTY_MENU_INDEX,
                label="Show Targets")

            # Unselected target when hiding because there is no point in
            # a user moving or deleting a target they can't see.
            self._canvas_manager.selection_update_listener(self._selected_target,
                                                       None)
            self._selected_target = None
        else:
            self._targets_menu.entryconfig(TARGET_VISIBILTY_MENU_INDEX,
                label="Hide Targets")

        self._show_targets = not self._show_targets

    def pause_shot_detection(self, pause):
        self._pause_shot_detection = pause

    def clear_shots(self):
        self._webcam_canvas.delete(SHOT_MARKER)
        self._shots = []

        self._shot_timer_start = None
        shot_entries = self._shot_timer_tree.get_children()
        for shot in shot_entries: 
            if self._shot_timer_tree.exists(shot):
                self._shot_timer_tree.delete(shot)
        self._previous_shot_time_selection = None

        self._webcam_canvas.focus_set()

    def reset_click(self):
        self.clear_shots()

        if self._loaded_training != None:
            targets = self._canvas_manager.aggregate_targets(self._targets)
            targets.extend(self._projector_arena.aggregate_targets())
            self._loaded_training.reset(targets)

        if self._preferences[configurator.USE_VIRTUAL_MAGAZINE]:
            self._virtual_magazine_rounds = self._preferences[configurator.VIRTUAL_MAGAZINE]

        if self.get_projector_arena().is_visible():
            self._projector_arena.reset()

    def quit(self):
        if self._loaded_training:
            self._loaded_training.destroy()

        if self._protocol_operations:
            self._protocol_operations.destroy()

        self._shutdown = True
        self._cv.release()
        self._window.quit()

    def canvas_click_red(self, event):
        if self._preferences[configurator.DEBUG]:
            self.handle_shot("red", event.x, event.y)

    def canvas_click_green(self, event):
        if self._preferences[configurator.DEBUG]:
            self.handle_shot("green", event.x, event.y)

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
        if self._loaded_training:
            self._loaded_training.destroy()
            self._protocol_operations.destroy()
            self._loaded_training = None
            self._projector_arena.set_training_protocol(self._loaded_training)

    def load_training(self, plugin):
        targets = self._canvas_manager.aggregate_targets(self._targets)
        targets.extend(self._projector_arena.aggregate_targets())

        if self._loaded_training:
            self._loaded_training.destroy()

        if self._protocol_operations:
            self._protocol_operations.destroy()

        self._protocol_operations = ProtocolOperations(self._webcam_canvas, self)
        self._loaded_training = imp.load_module("__init__", *plugin).load(
            self._window, self._protocol_operations, targets)

        self._projector_arena.set_training_protocol(self._loaded_training)

    def edit_preferences(self):
        preferences_editor = PreferencesEditor(self._window, self._config_parser,
                                               self._preferences)

    def which(self, program):
        def is_exe(fpath):
            return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

        fpath, fname = os.path.split(program)
        if fpath:
            if is_exe(program):
                return program
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                path = path.strip('"')
                exe_file = os.path.join(path, program)
                if is_exe(exe_file):
                    return exe_file

        return None

    def save_feed_image(self):
        # If ghostscript is not installed, you can only save as an EPS.
        # This is because of the way images are saved (see below).
        filetypes = []

        if (self.which("gs") is None and self.which("gswin32c.exe") is None
            and self.which("gswin64c.exe") is None):
            filetypes=[("Encapsulated PostScript", "*.eps")]
        else:
           filetypes=[("Portable Network Graphics", "*.png"),
                ("Encapsulated PostScript", "*.eps"),
                ("GIF", "*.gif"), ("JPEG", "*.jpeg")]

        image_file = tkFileDialog.asksaveasfilename(
            filetypes=filetypes,
            title="Save ShootOFF Webcam Feed",
            parent=self._window)

        if not image_file: return

        file_name, extension = os.path.splitext(image_file)

        # The Tkinter canvas only supports saving its contents in postscript,
        # so if the user wanted something different we should convert the
        # postscript file using PIL then delete the temporary postscript file.
        # PIL can only open an eps file is Ghostscript is installed.
        if ".eps" not in extension:
            self._webcam_canvas.postscript(file=(file_name + "tmp.eps"))
            img = Image.open(file_name + "tmp.eps", "r")
            img.save(image_file, extension[1:])
            del img
            os.remove(file_name + "tmp.eps")
        else:
            self._webcam_canvas.postscript(file=(file_name + ".eps"))

    def shot_time_selected(self, event):
        selected_shots = event.widget.selection()

        if self._previous_shot_time_selection is not None:
            for shot in self._previous_shot_time_selection:
                shot.toggle_selected()

        self._previous_shot_time_selection = []

        for shot in selected_shots:
            shot_index = event.widget.index(shot)
            self._shots[shot_index].toggle_selected()
            self._previous_shot_time_selection.append(self._shots[shot_index])

        self._webcam_canvas.focus_set()

    def configure_default_shot_list_columns(self):
        self.configure_shot_list_columns(DEFAULT_SHOT_LIST_COLUMNS, [50, 50])

    def add_shot_list_columns(self, id_list):
        current_columns = self._shot_timer_tree.cget("columns")
        if not current_columns:
            self._shot_timer_tree.configure(columns=(id_list))
        else:
            self._shot_timer_tree.configure(columns=(current_columns + id_list))

    def resize_shot_list(self):
        self._shot_timer_tree.configure(displaycolumns="#all")

    # This method removes all but the default columns for the shot list
    def revert_shot_list_columns(self):
        self._shot_timer_tree.configure(columns=DEFAULT_SHOT_LIST_COLUMNS)
        self.configure_default_shot_list_columns()

        shot_entries = self._shot_timer_tree.get_children()
        for shot in shot_entries:
            current_values = self._shot_timer_tree.item(shot, "values")
            default_values = current_values[0:len(DEFAULT_SHOT_LIST_COLUMNS)]
            self._shot_timer_tree.item(shot, values=default_values)

        self.resize_shot_list()

    def configure_shot_list_columns(self, names, widths):
        for name, width in zip(names, widths):
            self.configure_shot_list_column(name, width)

        self.resize_shot_list()

    def append_shot_list_column_data(self, item, values):
        current_values = self._shot_timer_tree.item(item, "values")
        self._shot_timer_tree.item(item, values=(current_values + values))

    def configure_shot_list_column(self, name, width):
        self._shot_timer_tree.heading(name, text=name)
        self._shot_timer_tree.column(name, width=width, stretch=False)

    def open_projector_arena(self):
        self._projector_arena.toggle_visibility()
        self.toggle_projector_menus(True)

    def calibrate_projector(self):
        self._calibrate_projector = not self._calibrate_projector

        self._projector_arena.calibrate(self._calibrate_projector)

        if self._calibrate_projector:
            self._projector_calibrator.show_threshold_slider(self._window)

            self._projector_menu.entryconfig(PROJECTOR_CALIBRATE_MENU_INDEX, 
                label="Stop Calibrating")

            self.pause_shot_detection(True)
            self._projector_calibrated = False

        else:
            self._projector_calibrator.destroy_threshold_slider()

            self._projector_menu.entryconfig(PROJECTOR_CALIBRATE_MENU_INDEX,
                label="Calibrate")

            self.pause_shot_detection(False)

            if (self._projector_calibrator.get_projected_bbox() == (0, 0, 0, 0)):
                tkMessageBox.showerror("Couldn't Calibrate Projector Arena",
                    "A calibration lock was never achieved for the projector arena. " +
                    "Shots on the arena will not be detected.")
            else:
                self._projector_calibrated = True
                self._logger.info("Calibrated the projector arena with bbox: " + 
                    str(self._projector_calibrator.get_projected_bbox()))

    def toggle_projector_menus(self, state=True):
        if state:
            self._projector_menu.entryconfig(PROJECTOR_ARENA_MENU_INDEX, 
                state=Tkinter.DISABLED)
            self._projector_menu.entryconfig(PROJECTOR_CALIBRATE_MENU_INDEX, 
                state=Tkinter.NORMAL)
            self._projector_menu.entryconfig(PROJECTOR_ADD_TARGET_MENU_INDEX, 
                state=Tkinter.NORMAL)
        else:
            self._projector_menu.entryconfig(PROJECTOR_ARENA_MENU_INDEX, 
                state=Tkinter.NORMAL)
            self._projector_menu.entryconfig(PROJECTOR_CALIBRATE_MENU_INDEX, 
                state=Tkinter.DISABLED)
            self._projector_menu.entryconfig(PROJECTOR_ADD_TARGET_MENU_INDEX, 
                state=Tkinter.DISABLED)

    def get_projector_arena(self):
        return self._projector_arena

    def projector_arena_closed(self):
        if self._calibrate_projector:
            self.calibrate_projector()

        self.toggle_projector_menus(False)
        self._projector_calibrated = False        

    def build_gui(self, feed_dimensions=(640, 480)):
        # Create the main window
        self._window = Tkinter.Tk()

        self._projector_arena = ProjectorArena(self._window, self)

        try:
            if platform.system() == "Windows":            
                self._window.iconbitmap("images\windows_icon.ico")
            else:
                icon_img = Tkinter.PhotoImage(file=os.path.join("images", "icon_48x48.gif"))
                self._window.tk.call('wm','iconphoto', self._window._w, icon_img)
        except:
            self._logger.warning("Failed to set main window icon.")
            pass

        self._window.protocol("WM_DELETE_WINDOW", self.quit)
        self._window.title("ShootOFF")

        self._frame = ttk.Frame(self._window)
        self._frame.pack()

        # Create the container for our webcam image
        self._webcam_canvas = Tkinter.Canvas(self._frame,
            width=feed_dimensions[0]-1, height=feed_dimensions[1]-1)
        self._webcam_canvas.grid(row=0, column=0)

        self._webcam_canvas.bind('<ButtonPress-1>', self.canvas_click)
        self._webcam_canvas.bind('<Delete>', self.canvas_delete_target)
        # Click to shoot
        if self._preferences[configurator.DEBUG]:
            self._webcam_canvas.bind('<Shift-ButtonPress-1>', self.canvas_click_red)
            self._webcam_canvas.bind('<Control-ButtonPress-1>', self.canvas_click_green)

        self._canvas_manager = CanvasManager(self._webcam_canvas, self._image_regions_images)

        # Create a button to clear shots and reset the current training protocol
        self._reset_button = ttk.Button(
            self._frame, text="Reset", command=self.reset_click)
        self._reset_button.grid(row=1, column=0)

        # Create the shot timer tree
        self._shot_timer_tree = ttk.Treeview(self._frame, selectmode="extended",
                                             show="headings")
        self.add_shot_list_columns(DEFAULT_SHOT_LIST_COLUMNS)
        self.configure_default_shot_list_columns()

        tree_scrolly = ttk.Scrollbar(self._frame, orient=Tkinter.VERTICAL,
                                     command=self._shot_timer_tree.yview)
        self._shot_timer_tree['yscroll'] = tree_scrolly.set

        tree_scrollx = ttk.Scrollbar(self._frame, orient=Tkinter.HORIZONTAL,
                                     command=self._shot_timer_tree.xview)
        self._shot_timer_tree['xscroll'] = tree_scrollx.set

        self._shot_timer_tree.grid(row=0, column=1, rowspan=2, sticky=Tkinter.NSEW)
        tree_scrolly.grid(row=0, column=2, rowspan=2, stick=Tkinter.NS)
        tree_scrollx.grid(row=2, column=1, stick=Tkinter.EW)
        self._shot_timer_tree.bind("<<TreeviewSelect>>", self.shot_time_selected)

        self.create_menu()

    def create_menu(self):
        menu_bar = Tkinter.Menu(self._window)
        self._window.config(menu=menu_bar)

        file_menu = Tkinter.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="Preferences", command=self.edit_preferences)
        file_menu.add_command(label="Save Feed Image...", command=self.save_feed_image)
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
            self._targets_menu, "Edit Target", self.edit_target, True)
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

        # Create projector menu
        self._projector_menu = Tkinter.Menu(menu_bar, tearoff=False)
        self._projector_menu.add_command(label="Start Arena", 
            command=self.open_projector_arena)
        self._projector_menu.add_command(label="Calibrate", state=Tkinter.DISABLED, 
            command=self.calibrate_projector)
        self._add_projector_target_menu = self.create_target_list_menu(
            self._projector_menu, "Add Target", self._projector_arena.add_target, True)
        self._projector_menu.entryconfig(PROJECTOR_ADD_TARGET_MENU_INDEX, 
            state=Tkinter.DISABLED)
        menu_bar.add_cascade(label="Projector", menu=self._projector_menu)

    def callback_factory(self, func, name):
        return lambda: func(name)

    def create_target_list_menu(self, menu, name, func, include_animated=False):
        targets = glob.glob("targets/*.target")
        
        if include_animated:
            targets.extend(glob.glob("animated_targets/*.target"))

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

    def __init__(self, config):
        self._shots = []
        self._targets = []
        self._image_regions_images = {}
        self._refresh_miss_count = 0
        self._show_targets = True
        self._selected_target = ""
        self._loaded_training = None
        self._seen_interference = False
        self._show_interference = False
        self._webcam_frame = None
        self._config_parser = config.get_config_parser()
        self._preferences = config.get_preferences()
        self._shot_timer_start = None
        self._previous_shot_time_selection = None
        self._logger = config.get_logger()
        self._virtual_magazine_rounds = -1
        self._projector_calibrator = ProjectorCalibrator()
        self._calibrate_projector = False
        self._projector_calibrated = False

        self._cv = cv2.VideoCapture(self._preferences[configurator.VIDCAM])

        if self._cv.isOpened():
            width = self._cv.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)
            height = self._cv.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)

            # If the resolution is too low, try to force it higher.
            # Some users have drivers that default to extremely low
            # resolutions and opencv doesn't currently make it easy
            # to enumerate valid resolutions and switch to them
            if width < 640 and height < 480:
                self._logger.info("Webcam resolution is current low (%dx%d), " +
                                 "attempting to increase it to 640x480", width, height)
                self._cv.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 640)
                self._cv.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 480)
                width = self._cv.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)
                height = self._cv.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)

            self._logger.debug("Webcam resolution is %dx%d", width, height)
            self.build_gui((width, height))
            self._protocol_operations = ProtocolOperations(self._webcam_canvas, self)

            fps = self._cv.get(cv2.cv.CV_CAP_PROP_FPS)
            if fps <= 0:
                self._logger.info("Couldn't get webcam FPS, defaulting to 30.")
            else:
                FEED_FPS = fps
                self._logger.info("Feed FPS set to %d.", fps)

            # Webcam related threads will end when this is true
            self._shutdown = False

            #Start the refresh loop that shows the webcam feed
            self._refresh_thread = Thread(target=self.refresh_frame,
                                          name="refresh_thread")
            self._refresh_thread.start()

            #Start the shot detection loop
            self._pause_shot_detection = False
            self._shot_detection_thread = Thread(target=self.detect_shots,
                                                 name="shot_detection_thread")
            self._shot_detection_thread.start()
        else:
            tkMessageBox.showwarning("Open Video Camera",
                "Cannot open this vidcam (%d)\n" % self._preferences[configurator.VIDCAM])
			
            tkMessageBox.showerror("Couldn't Connect to Webcam", "Video capturing " +
                "could not be initialized either because there is no webcam or " +
                "we cannot connect to it. ShootOFF will shut down.")
            self._logger.critical("Video capturing could not be initialized either " +
                "because there is no webcam or we cannot connect to it.")
            self._shutdown = True

    def main(self):
        if not self._shutdown:
            Tkinter.mainloop()
            self._window.destroy()

if __name__ == "__main__":
    config = Configurator()

    preferences = config.get_preferences()
    logger = config.get_logger()

    logger.debug(preferences)

    # Start the main window
    mainWindow = MainWindow(config)
    mainWindow.main()
