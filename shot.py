# Copyright (c) 2013 phrack. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import cv2

class Shot:
    # Use the default color and radius for the
    # shot marker. Create a new shoot at coord
    # (a tuple representing the coordinate of 
    # laser on the webcam feed).
    def __init__(self, coord, marker_radius=2, marker_color="green2"):
        self._marker_color = marker_color
        self._marker_radius = marker_radius
        self._coord = coord

    def set_marker_color(self, marker_color):
        self._marker_color = marker_color

    def set_marker_radius(self, marker_radius):
        self._marker_radius = marker_radius

    def get_color(self):
        return self._marker_color

    def get_coords(self):
        return self._coord

    def draw_marker(self, canvas):
        x = self._coord[0]
        y = self._coord[1]

        canvas.create_oval(
            x - self._marker_radius,
            y - self._marker_radius,
            x + self._marker_radius,
            y + self._marker_radius, 
            fill=self._marker_color, outline=self._marker_color, 
            tags=("shot_marker"))

