# Copyright (c) 2013 phrack. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import cv2

class Shot:
    # Use the default color and radius for the
    # shot marker. Create a new shoot at coord
    # (a tuple representing the coordinate of 
    # laser on the webcam feed).
    def __init__(self, coord, marker_radius=2):
        self._marker_color = (0,255,0) # default bright green
        self._marker_radius = marker_radius
        self._coord = coord

    def set_marker_color(self, marker_color):
        self._marker_color = marker_color

    def set_marker_radius(self, marker_radius):
        self._marker_radius = marker_radius

    def get_coords(self):
        return self._coord

    def draw_marker(self, frame):
        cv2.circle(frame, self._coord, self._marker_radius, 
            self._marker_color, -1)
