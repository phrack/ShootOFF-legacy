# Copyright (c) 2014 phrack. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from canvas_manager import CanvasManager
from tag_parser import TagParser
import Tkinter, ttk

class ProjectorArena():
    def handle_shot(self, laser_color, x, y):
        hit_region = None
        hit_tags = None
        regions = self._arena_canvas.find_overlapping(x, y, x, y)

        # If we hit a targert region, run its commands and notify the
        # loaded plugin of the hit
        for region in reversed(regions):
            tags = TagParser.parse_tags(self._arena_canvas.gettags(region))

            if "_internal_name" in tags and "command" in tags:
                self._canvas_manager.execute_region_commands(region, tags["command"], 
                    self._shootoff.get_protocol_operations())

            if "_internal_name" in tags and self._loaded_training != None:
                hit_region = region
                hit_tags = TagParser.parse_tags(self._arena_canvas.gettags(region))

            if "_internal_name" in tags:
                is_hit = True
                # only run the commands and notify a hit for the top most
                # region
                break

        # Also run commands for all hidden regions that were hit
        for region in regions:
            tags = TagParser.parse_tags(self._arena_canvas.gettags(region))

            if "visible" in tags and "command" in tags and tags["visible"].lower() == "false":                
                self._canvas_manager.execute_region_commands(region, tags["command"], 
                    self._shootoff.get_protocol_operations())
     
        return hit_region, hit_tags

    def reset(self):
        self._canvas_manager.reset_animations()
    
    def toggle_fullscreen(self, event=None):
        self._fullscreen = not self._fullscreen

        if self._fullscreen:
            self._old_window_width = self._window.winfo_width()
            self._old_window_height = self._window.winfo_height()
            self._arena_canvas.configure(width=self._window.winfo_screenwidth(), height=self._window.winfo_screenheight())
            width_scale = float(self._window.winfo_screenwidth())  / float(self._old_window_width)
            height_scale = float(self._window.winfo_screenheight())  / float(self._old_window_height)
            self._arena_canvas.scale("background", 0, 0, width_scale, height_scale)
        else:
            self._arena_canvas.configure(width=self._window.winfo_width(), height=self._window.winfo_height())
            width_scale = float(self._old_window_width)  / float(self._window.winfo_screenwidth())
            height_scale = float(self._old_window_height)  / float(self._window.winfo_screenheight())
            self._arena_canvas.scale("background", 0, 0, width_scale, height_scale)
     
        self._window.attributes("-topmost", self._fullscreen)
        self._window.attributes("-fullscreen", self._fullscreen)

        if not self._fullscreen:
            self._window.geometry("%sx%s" % (self._old_window_width,
                    self._old_window_height))

    def calibrate(self, calibration=True):
        if calibration:
            # This is to cover existing targets
            self._arena_canvas.create_rectangle(0, 0, self._arena_canvas.winfo_width(), 
                self._arena_canvas.winfo_height(), fill="black", tags=("target_cover"))

            x = self._window.winfo_width()
            y = self._window.winfo_height()

            self._arena_canvas.create_polygon(0, 0, 250, 0, 125, 250, 0, 0, 
                fill="white", tags=("top_left_calibrator"))
            self._arena_canvas.create_rectangle(x-250, y-125, x, y, 
                fill="white", tags=("bottom_right_calibrator"))
        else:
            self._arena_canvas.delete("target_cover")
            self._arena_canvas.delete("top_left_calibrator") 
            self._arena_canvas.delete("bottom_right_calibrator") 
    
    def aggregate_targets(self):
        return self._canvas_manager.aggregate_targets(self._targets)
    
    def set_training_protocol(self, training):
        self._loaded_training = training

    def arena_width(self):
        return self._arena_canvas.winfo_width()

    def arena_height(self):
        return self._arena_canvas.winfo_height()

    def add_target(self, name):
        target_name = self._canvas_manager.add_target(name, self._image_regions_images)
        self._targets.append(target_name)

        if len(self._arena_canvas.find_withtag("target_cover")) > 0:
            self._arena_canvas.tag_lower(target_name, "target_cover")

    def toggle_visibility(self):
        if self._visible:
            self._shootoff.projector_arena_closed()
            self._window.withdraw()
        else:
            self._window.update()
            self._window.deiconify()

        self._visible = not self._visible

    def canvas_click(self, event):
        # find the target that was selected
        # if a target wasn't clicked, _selected_target
        # will be empty and all targets will be dim
        selected_region = event.widget.find_closest(
            event.x, event.y)
        target_name = ""

        for tag in self._arena_canvas.gettags(selected_region):
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

    def build_gui(self, parent):
        self._window = Tkinter.Toplevel(parent)
        self._window.title("Projector Arena")
        self._window.configure(background="black")
        self._window.protocol("WM_DELETE_WINDOW", self.toggle_visibility)
        self._window.withdraw()

        self._window.configure(highlightcolor="black")

        self._frame = ttk.Frame(self._window)
        self._frame.pack()

        self._arena_canvas = Tkinter.Canvas(self._frame, 
            width=600, height=480, background="gray15", bd=-1)
        self._arena_canvas.pack()

        self._arena_canvas.bind('<ButtonPress-1>', self.canvas_click)
        self._arena_canvas.bind('<Delete>', self.canvas_delete_target)
        self._arena_canvas.create_rectangle(0, 0, 600, 480, fill="gray15", outline="gray15", tags=("background"))

        self._canvas_manager = CanvasManager(self._arena_canvas, self._image_regions_images)

        self._window.bind("<F11>", self.toggle_fullscreen);  

        self._frame.pack()

    def __init__(self, parent, shootoff):
        self._visible = False
        self._fullscreen = False
        self._shootoff = shootoff
        self._targets = []
        self._selected_target = ""        
        self._image_regions_images = {}
        self._loaded_training = None

        self.build_gui(parent)
