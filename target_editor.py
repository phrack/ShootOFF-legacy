# Copyright (c) 2013 phrack. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from canvas_manager import CanvasManager
import os
from PIL import Image, ImageTk
from tag_editor_popup import TagEditorPopup
from target_pickler import TargetPickler
import Tkinter, tkFileDialog, ttk

CURSOR = 0
RECTANGLE = 1
OVAL = 2
TRIANGLE = 3

CANVAS_BACKGROUND = (1,)

class TargetEditor():
    def save_target(self):
        target_file = tkFileDialog.asksaveasfilename(
            defaultextension=".target",
            filetypes=[("ShootOFF Target", ".target")],
            initialdir="targets/",
            title="Save ShootOFF Target",
            parent=self._window)

        if (target_file and not os.path.isfile(target_file)):
            self._notify_new_target(target_file)

        if target_file:
            target_pickler = TargetPickler()
            target_pickler.save(target_file, self._regions,
                self._target_canvas)

    def color_selected(self, event):
        if (self._selected_region is not None and
            self._selected_region != CANVAS_BACKGROUND):               

            self._target_canvas.itemconfig(self._selected_region,
                fill=self._fill_color_combo.get())

    def bring_forward(self):
        if (self._selected_region is not None and
            self._selected_region != CANVAS_BACKGROUND):
            
            below = self._target_canvas.find_above(self._selected_region)
            
            if len(below) > 0:
                self._target_canvas.tag_raise(self._selected_region,
                    below)

                # we have to change the order in the regions list
                # as well so the z order is maintained during pickling
                self.reverse_regions(below, self._selected_region)

    def send_backward(self):
        if (self._selected_region is not None and
            self._selected_region != CANVAS_BACKGROUND):
            
            above = self._target_canvas.find_below(self._selected_region)
            
            if len(above) > 0:
                self._target_canvas.tag_lower(self._selected_region,
                    above)

                # we have to change the order in the regions list
                # as well so the z order is maintained during pickling
                self.reverse_regions(above, self._selected_region)

    def reverse_regions(self, region1, region2):
        r1 = self._regions.index(region1[0])
        r2 = self._regions.index(region2[0])

        self._regions[r2], self._regions[r1] = self._regions[r1], self._regions[r2]

    def canvas_click(self, event):
        if self._radio_selection.get() != CURSOR:
            # This will make it so that mouse move event
            # won't delete the current cursor shape and will
            # make a new one, thus leaving the current shape 
            # as a region
            self._regions.append(self._cursor_shape)
            self._cursor_shape = None
        else:
            old_region = self._selected_region
            self._selected_region = event.widget.find_closest(
                event.x, event.y)  

            self._canvas_manager.selection_update_listener(old_region,
                self._selected_region)

            if self._selected_region != CANVAS_BACKGROUND:
                self._fill_color_combo.configure(state="readonly") 
                self._fill_color_combo.set(
                    event.widget.itemcget(self._selected_region, "fill"))

                self._tags_button.configure(state=Tkinter.NORMAL)

                if self._tag_popup_state.get()==True:
                    self.toggle_tag_editor()
            else:
                self._fill_color_combo.configure(state=Tkinter.DISABLED)  
                self._tags_button.configure(state=Tkinter.DISABLED)  

                if self._tag_popup_state.get()==True:
                    self._tag_popup_state.set(False)
                    self.toggle_tag_editor()

    def canvas_mouse_move(self, event):
        if self._cursor_shape is not None:
            self._target_canvas.delete(self._cursor_shape)
        
        if self._radio_selection.get() == CURSOR:
            self._cursor_shape = None

        initial_size = 30

        if self._radio_selection.get() == RECTANGLE:        
            self._cursor_shape = self._target_canvas.create_rectangle(
                event.x - initial_size,
                event.y - initial_size,
                event.x + initial_size,
                event.y + initial_size, 
                fill="black", stipple="gray25", tags=("_shape:rectangle"))

        elif self._radio_selection.get() == OVAL:        
            self._cursor_shape = self._target_canvas.create_oval(
                event.x - initial_size,
                event.y - initial_size,
                event.x + initial_size,
                event.y + initial_size, 
                fill="black", stipple="gray25", tags=("_shape:oval"))

        elif self._radio_selection.get() == TRIANGLE:        
            self._cursor_shape = self._target_canvas.create_polygon(
                event.x,
                event.y - initial_size,
                event.x + initial_size,
                event.y + initial_size,
                event.x - initial_size,
                event.y + initial_size, 
                event.x,
                event.y - initial_size,
                fill="black", outline="black", stipple="gray25",
                tags=("_shape:triangle"))

    def canvas_delete_region(self, event):
        if (self._selected_region is not None and
            self._selected_region != CANVAS_BACKGROUND):
            
            for shape in self._selected_region:
                self._regions.remove(shape)
            event.widget.delete(self._selected_region)
            self._selected_region = None

    def toggle_tag_editor(self):
        if self._tag_popup_state.get()==True:
            x = (self._tags_button.winfo_x() + 
                (self._tags_button.winfo_width() / 2))
            y = (self._tags_button.winfo_y() +
                (self._tags_button.winfo_height() * 1.5))

            self._tag_editor.show(
                self._target_canvas.gettags(self._selected_region), x, y)
        else:
            self._tag_editor.hide()

    def update_tags(self, new_tag_list):
        # delete all of the non-internal tags
        for tag in self._target_canvas.gettags(self._selected_region):
            if not tag.startswith("_"):
                self._target_canvas.dtag(self._selected_region,
                   tag)

        # add all tags in the new tag list        
        tags = self._target_canvas.gettags(self._selected_region)
        self._target_canvas.itemconfig(self._selected_region, 
            tags=tags + new_tag_list)

    def build_gui(self, parent, webcam_image):
        # Create the main window
        self._window = Tkinter.Toplevel(parent)
        self._window.transient(parent)
        self._window.title("Target Editor")

        self._frame = ttk.Frame(self._window)
        self._frame.pack(padx=15, pady=15)

        self.create_toolbar(self._frame)
 
        # Create tags popup frame
        self._tag_editor = TagEditorPopup(self._window, self.update_tags)

        # Create the canvas the target will be drawn on
        # and show the webcam frame in it
        self._webcam_image = webcam_image

        self._target_canvas = Tkinter.Canvas(self._frame, 
            width=webcam_image.width(), height=webcam_image.height()) 
        self._target_canvas.create_image(0, 0, image=self._webcam_image,
            anchor=Tkinter.NW, tags=("background"))
        self._target_canvas.pack()

        self._target_canvas.bind('<ButtonPress-1>', self.canvas_click)
        self._target_canvas.bind('<Motion>', self.canvas_mouse_move)
        self._target_canvas.bind('<Delete>', self.canvas_delete_region)

        self._canvas_manager = CanvasManager(self._target_canvas)

    def create_toolbar(self, parent):
       # Create the toolbar
        toolbar = Tkinter.Frame(parent, bd=1, relief=Tkinter.RAISED)
        self._radio_selection = Tkinter.IntVar()
        self._radio_selection.set(CURSOR)

        # Save button
        self._save_icon = Image.open("images/gnome_media_floppy.png")
        self.create_toolbar_button(toolbar, self._save_icon, 
            self.save_target)
        
        # cursor button
        self._cursor_icon = Image.open("images/cursor.png")
        self.create_radio_button(toolbar, self._cursor_icon, CURSOR)

        # rectangle button
        self._rectangle_icon = Image.open("images/rectangle.png")
        self.create_radio_button(toolbar, self._rectangle_icon, RECTANGLE)

        # oval button
        self._oval_icon = Image.open("images/oval.png")
        self.create_radio_button(toolbar, self._oval_icon, OVAL)

        # triangle button
        self._triangle_icon = Image.open("images/triangle.png")
        self.create_radio_button(toolbar, self._triangle_icon, TRIANGLE)

        # bring forward button
        self._bring_forward_icon = Image.open("images/bring_forward.png")
        self.create_toolbar_button(toolbar, self._bring_forward_icon, 
            self.bring_forward)

        # send backward button
        self._send_backward_icon = Image.open("images/send_backward.png")
        self.create_toolbar_button(toolbar, self._send_backward_icon, 
            self.send_backward)

        # show tags button
        tags_icon = ImageTk.PhotoImage(Image.open("images/tags.png"))  

        self._tag_popup_state = Tkinter.IntVar()
        self._tags_button = Tkinter.Checkbutton(toolbar,
            image=tags_icon, indicatoron=False, variable=self._tag_popup_state,
            command=self.toggle_tag_editor, state=Tkinter.DISABLED)
        self._tags_button.image = tags_icon
        self._tags_button.pack(side=Tkinter.LEFT, padx=2, pady=2)

        # color chooser
        self._fill_color_combo = ttk.Combobox(toolbar,
            values=["black", "blue", "green", "orange", "red", "white"],
            state="readonly")
        self._fill_color_combo.set("black")
        self._fill_color_combo.bind("<<ComboboxSelected>>", self.color_selected)
        self._fill_color_combo.configure(state=Tkinter.DISABLED)
        self._fill_color_combo.pack(side=Tkinter.LEFT, padx=2, pady=2)

        toolbar.pack(fill=Tkinter.X)

    def create_radio_button(self, parent, image, selected_value):
        icon = ImageTk.PhotoImage(image)  

        button = Tkinter.Radiobutton(parent, image=icon,              
            indicatoron=False, variable=self._radio_selection,
            value=selected_value)
        button.image = icon
        button.pack(side=Tkinter.LEFT, padx=2, pady=2)

    def create_toolbar_button(self, parent, image, command, enabled=True):
        icon = ImageTk.PhotoImage(image)  

        button = Tkinter.Button(parent, image=icon, relief=Tkinter.RAISED, command=command)

        if not enabled:
            button.configure(state=Tkinter.DISABLED)

        button.image = icon
        button.pack(side=Tkinter.LEFT, padx=2, pady=2)

    # target is set when we are editing a target,
    # otherwise we are creating a new target

    # notifynewfunc is a callback that can be set to see
    # when a new target is saved (e.g. the save button is
    # hit AND results in a new file). The callback takes
    # one parameter (the targets file name)
    def __init__(self, parent, webcam_image, target=None,
        notifynewfunc=None):

        self._cursor_shape = None
        self._selected_region = None
        self._regions = []
        self.build_gui(parent, webcam_image)

        if target is not None:
            target_pickler = TargetPickler()
            (region_object, self._regions) = target_pickler.load(
                target, self._target_canvas)

        self._notify_new_target = notifynewfunc
