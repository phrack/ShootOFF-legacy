# Copyright (c) 2014 phrack. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import Tkinter, ttk

class ProjectorArena():
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
            self._arena_canvas.create_polygon(0, 0, 10, 0, 5, 10, 0, 0, fill="green", tags=("top_left_calibrator"))
        else:
            self._arena_canvas.delete("top_left_calibrator") 

    def build_gui(self, parent):
        self._window = Tkinter.Toplevel(parent)
        self._window.title("Projector Arena")
        self._window.configure(background="black")

        self._window.configure(highlightcolor="black")

        self._frame = ttk.Frame(self._window)
        self._frame.pack()

        self._arena_canvas = Tkinter.Canvas(self._frame, 
            width=600, height=480, background="gray15", bd=-1)
        self._arena_canvas.pack()

        self._window.bind("<F11>", self.toggle_fullscreen);  

        self._frame.pack()

    def __init__(self, parent):
        self._fullscreen = False

        self.build_gui(parent)
