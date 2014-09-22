# Copyright (c) 2014 phrack. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import cv2
import math

class ProjectorCalibrator():
    def get_projected_bbox(self):
        return (self._top_x, self._top_y, self._bottom_x, self._bottom_y)

    def calibrate_projector(self, webcam_image):
        bw = cv2.cvtColor(webcam_image, cv2.cv.CV_BGR2GRAY)
        (thresh, bw_image) = cv2.threshold(bw, 200, 255, cv2.THRESH_BINARY)
        contours,h = cv2.findContours(bw_image, cv2.cv.CV_RETR_EXTERNAL,
                        cv2.cv.CV_CHAIN_APPROX_SIMPLE)

        self._top_x = 0
        self._top_y = 0
        self._bottom_x = 0
        self._bottom_y = 0

        detected_triangle = False
        detected_rectangle = False

        for cnt in contours:
            approx = cv2.approxPolyDP(cnt,0.01*cv2.arcLength(cnt,True),True)

            # Detect green triangle in top left corner
            if len(approx) == 3:
                detected_triangle = True
    
                self._top_x, self._top_y = self.far_left_coord(approx)

                cv2.drawContours(webcam_image, [approx], 0, (0,255,0), -1)
                cv2.circle(webcam_image, (self._top_x, self._top_y), 
                    10, (0,255,0))

            # Detect red rectangle in bottom right corner
            elif len(approx) == 4:
                detected_rectangle = True
                self._bottom_x, self._bottom_y = self.farthest_coord(approx)

                cv2.drawContours(webcam_image, [approx], 0, (255,0,0), -1)
                cv2.circle(webcam_image, (self._bottom_x, self._bottom_y), 
                    10, (0,255,0))

        # Draw bounding box for projector arena
        if detected_triangle and detected_rectangle:
            cv2.rectangle(webcam_image, (self._top_x, self._top_y), 
                (self._bottom_x, self._bottom_y), (255,255,0))

        return webcam_image

    def far_left_coord(self, coords):
        far_left_coord = []
        for coord in coords:
            if len(far_left_coord) == 0:
                far_left_coord = coord[0]
            else:
                if (coord[0][0] <= far_left_coord[0]):
                    far_left_coord = coord[0]

        return far_left_coord[0], far_left_coord[1]

    def farthest_coord(self, coords):
        farthest_distance = 0
        farthest_coord = []

        for coord in coords:
            if farthest_distance == 0:
                farthest_distance = self.distance_from_origin(coord[0])
                farthest_coord = coord[0]
            else:
                cur_distance = self.distance_from_origin(coord[0])
                if cur_distance >= farthest_distance:
                    farthest_distance = cur_distance
                    farthest_coord = coord[0]

        return farthest_coord[0], farthest_coord[1]     

    def distance_from_origin(self, coord):
        return math.sqrt(coord[0]*2 + coord[1]*2)

    def __init__(self):
    	pass
