# Copyright (c) 2013 phrack. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import cv2

class Shot:
    # Use the default color and radius for the
    # shot marker. Create a new shoot at coord
    # (a tuple representing the coordinate of 
    # laser on the webcam feed). The timestamp
    # is the shot timer's time stamp when the
    # shot was detected.
    def __init__(self, coord, canvas, marker_radius=2, marker_color="green2", timestamp=0):
        self._marker_color = marker_color
        self._marker_radius = marker_radius
        self._coord = coord
        self._canvas = canvas
        self._timestamp = timestamp
        self._canvas_id = None
        self._is_selected = False

    def set_marker_color(self, marker_color):
        self._marker_color = marker_color
        self._canvas.itemconfig(self._canvas_id, fill=marker_color)

    def set_marker_radius(self, marker_radius):
        self._marker_radius = marker_radius

	    # Redraw the marker with the new radius
        self._canvas.delete(self._canvas_id)
        self.draw_marker()

    def get_color(self):
        return self._marker_color

    def get_coords(self):
        return self._coord

    def get_timestamp(self):
        return self._timestamp

    def draw_marker(self):
        x = self._coord[0]
        y = self._coord[1]

        self._canvas_id = self._canvas.create_oval(
            x - self._marker_radius,
            y - self._marker_radius,
            x + self._marker_radius,
            y + self._marker_radius, 
            fill=self._marker_color, outline=self._marker_color, 
            tags=("shot_marker"))

    def toggle_selected(self):
        self._is_selected = not self._is_selected 
        if self._is_selected:
            # Selected shots have cyan outlines
            self._canvas.itemconfig(self._canvas_id, fill="gold", outline="gold")   
            self._canvas.tag_raise(self._canvas_id)
        else:
            self._canvas.itemconfig(self._canvas_id, fill=self._marker_color, 
                outline=self._marker_color)

