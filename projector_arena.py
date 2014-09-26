# Copyright (c) 2014 phrack. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from canvas_manager import CanvasManager
import Tkinter, ttk

class ProjectorArena():
    def handle_shot(self, laser_color, x, y):
        self._arena_canvas.create_oval(
            x - 2,
            y - 2,
            x + 2,
            y + 2, 
            fill=laser_color, outline=laser_color, 
            tags=("shot_marker"))        

    def toggle_fullscreen(self, event=None):
        self._fullscreen = not self._fullscreen
        self._window.attributes("-fullscreen", self._fullscreen)

        if self._fullscreen:
            self._arena_canvas.configure(width=self._window.winfo_screenwidth())
            self._arena_canvas.configure(height=self._window.winfo_screenheight())
        else:
            self._arena_canvas.configure(width=self._window.winfo_width())
            self._arena_canvas.configure(height=self._window.winfo_height())

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
        
    def arena_width(self):
        return self._arena_canvas.winfo_width()

    def arena_height(self):
        return self._arena_canvas.winfo_height()

    def add_target(self, name):
        target_name = self._canvas_manager.add_target(name, self._image_regions_images)
        self._targets.append(target_name)

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

        self.build_gui(parent)
