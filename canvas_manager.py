# Copyright (c) 2013 phrack. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# This class manages operations common to the webcam feed canvas
# and the target editor canvas
class CanvasManager():
    def selection_update_listener(self, old_selection, new_selection):
        self._selection = new_selection

        # brighten the old selection
        if (old_selection and
            not self.is_background(old_selection)):

            self._canvas.itemconfig(old_selection, stipple="gray25")  
    
        #darken the new one
        if (new_selection and
            not self.is_background(new_selection)):
            
            self._canvas.itemconfig(new_selection, stipple="gray50")   

    def move_region(self, event):
        if (self._selection and 
            not self.is_background(self._selection)):

            if event.keysym == "Up":
                event.widget.move(self._selection, 0, -1)
            elif event.keysym == "Down":
                event.widget.move(self._selection, 0, 1)
            elif event.keysym == "Right":
                event.widget.move(self._selection, 1, 0)
            elif event.keysym == "Left":
                event.widget.move(self._selection, -1, 0)

    def scale_region(self, event):
        if (not self._selection or 
            self.is_background(self._selection)):
            return

        c = event.widget.coords(self._selection)

        # The region is scaled by a ratio, so we need to know the current
        # dimension so that we can calculate the ratio needed to scale
        # the selection by only one pixel
        width = c[2] - c[0]
        height = c[3] - c[1]

        if event.keysym == "Up":
            event.widget.scale(self._selection, c[0], c[1], 1, (height-1)/height)
        elif event.keysym == "Down" and height > 1:
            event.widget.scale(self._selection, c[0], c[1], 1, (height+1)/height)
        elif event.keysym == "Right":
            event.widget.scale(self._selection, c[0], c[1], (width+1)/width, 1)
        elif event.keysym == "Left" and width > 1:
            event.widget.scale(self._selection, c[0], c[1], (width-1)/width, 1)

    def is_background(self, selection):
        if "background" in self._canvas.gettags(selection):
            return True

        return False

    def __init__(self, canvas):
        canvas.bind('<Up>', self.move_region)
        canvas.bind('<Down>', self.move_region)
        canvas.bind('<Left>', self.move_region)
        canvas.bind('<Right>', self.move_region)
        canvas.bind('<Shift-Up>', self.scale_region)
        canvas.bind('<Shift-Down>', self.scale_region)
        canvas.bind('<Shift-Left>', self.scale_region)
        canvas.bind('<Shift-Right>', self.scale_region)

        canvas.focus_set()

        self._canvas = canvas
        self._selection = None
