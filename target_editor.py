# Copyright (c) 2013 phrack. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import canvas_manager
from canvas_manager import CanvasManager
import os
from PIL import Image, ImageTk
from tag_editor_popup import TagEditorPopup
from target_pickler import TargetPickler
import Tkinter, tkFileDialog, tkMessageBox, ttk

CURSOR = 0
IMAGE = 1
RECTANGLE = 2
OVAL = 3
TRIANGLE = 4
FREEFORM_POLYGON = 5
D_SILHOUETTE_3 = 6
D_SILHOUETTE_4 = 7
D_SILHOUETTE_5 = 8

CANVAS_BACKGROUND = (1,)

class TargetEditor():
    def save_target(self):
        is_animated = self._canvas_manager.is_animated(self._regions)
        if is_animated:
            initdir = "animated_targets/"
        else:
            initdir = "targets/"

        target_file = tkFileDialog.asksaveasfilename(
            defaultextension=".target",
            filetypes=[("ShootOFF Target", ".target")],
            initialdir=initdir,
            title="Save ShootOFF Target",
            parent=self._window)

        is_new_target = target_file and not os.path.isfile(target_file)

        if target_file:
            target_pickler = TargetPickler()
            target_pickler.save(target_file, self._regions,
                self._target_canvas)

        if (is_new_target):
            self._notify_new_target(target_file, is_animated)

    def color_selected(self, event):
        self._target_canvas.focus_set()

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

            if len(above) > 0  and above != CANVAS_BACKGROUND:
                self._target_canvas.tag_lower(self._selected_region,
                    above)

                # we have to change the order in the regions list
                # as well so the z order is maintained during pickling
                self.reverse_regions(above, self._selected_region)

    def reverse_regions(self, region1, region2):
        r1 = self._regions.index(region1[0])
        r2 = self._regions.index(region2[0])

        self._regions[r2], self._regions[r1] = self._regions[r1], self._regions[r2]

    def undo_vertex(self, event):
        if self._radio_selection.get() == FREEFORM_POLYGON:
            # Remove the last vertex (if there is 
            if len(self._freeform_vertices_ids) > 0:
                self._target_canvas.delete(self._freeform_vertices_ids[-1])
                del self._freeform_vertices_points[-1]
                del self._freeform_vertices_ids[-1]           

            # Remove the last edge (if there is one)
            if len(self._freeform_edges_ids) > 0:
                self._target_canvas.delete(self._freeform_edges_ids[-1])
                del self._freeform_edges_ids[-1]

            if self._freeform_temp_line_id is not None:
                self._target_canvas.delete(self._freeform_temp_line_id)
                self._freeform_temp_line_id = None

    def _reset_freeform_polygon(self):
        self._target_canvas.delete("_shape:vertex")
        self._target_canvas.delete("_shape:freeform_edge")

        self._freeform_vertices_points = []
        self._freeform_vertices_ids = []
        self._freeform_edges_ids = []
        self._freeform_temp_line_id = None

    def radio_button_click(self):
        if self._radio_selection.get() != FREEFORM_POLYGON:
            self._reset_freeform_polygon()

        if self._radio_selection.get() == IMAGE:
            image_file = tkFileDialog.askopenfilename(defaultextension=".*",
                filetypes=[("Graphics Interchange Format", ".gif"), 
                    ("Portable Network Graphic", ".png")],
                initialdir="animated_targets/",
                title="Open Target Image",
                parent=self._window)

            if image_file == None or len(image_file) == 0:
                self._radio_selection.set(CURSOR)
                return

            self._image_path = os.path.relpath(image_file)

    def canvas_right_click(self, event):
        if self._radio_selection.get() == FREEFORM_POLYGON:
            if len(self._freeform_vertices_points) < 4:
                tkMessageBox.showerror("Invalid Regular Polygon",
                    "A freeform polygon must have at least 3 vertices and should be " +
                    "closed.",
                    parent=self._frame)
                return

            # Make the last region the same as the first region, otherwise
            # they might not line up
            self._freeform_vertices_points[-1] = self._freeform_vertices_points[0]

            # Create the new region
            self._freeform_region = self._target_canvas.create_polygon(
                self._freeform_vertices_points,
                fill="black", outline="black", stipple="gray25",
                tags=("_shape:freeform_polygon"))
            self._regions.append(self._freeform_region)
            self._create_cursor_shape(event)

            # Delete all temporary data and shapes
            self._reset_freeform_polygon()

    def canvas_click(self, event):
        if self._radio_selection.get() == FREEFORM_POLYGON:
            self._freeform_vertices_points.append((event.x, event.y))
            self._freeform_vertices_ids.append(self._cursor_shape)

            if self._freeform_temp_line_id is not None:
                self._freeform_edges_ids.append(self._freeform_temp_line_id)

            self._create_cursor_shape(event)

        elif self._radio_selection.get() == IMAGE:
            # Make image a part of the target
            image = self._canvas_manager.cache_image_frames(self._cursor_shape, self._image_path)
            self._target_canvas.itemconfig(self._cursor_shape, image=image)

            self._canvas_manager.animate(self._cursor_shape, image)

            self._regions.append(self._cursor_shape)   
            self._create_cursor_shape(event) 

        elif self._radio_selection.get() != CURSOR:
            # This will make it so that mouse move event
            # won't delete the current cursor shape and will
            # make a new one, thus leaving the current shape 
            # as a region
            self._regions.append(self._cursor_shape)
            self._create_cursor_shape(event)

        else:
            old_region = self._selected_region
            self._selected_region = event.widget.find_closest(
                event.x, event.y)  

            self._canvas_manager.selection_update_listener(old_region,
                self._selected_region)

            if self._selected_region != CANVAS_BACKGROUND:
                tags = self._target_canvas.gettags(self._selected_region)         
                if not "_shape:image" in tags:
                    self._fill_color_combo.configure(state="readonly") 
                    self._fill_color_combo.set(
                        event.widget.itemcget(self._selected_region, "fill"))
                else:
                    self._fill_color_combo.configure(state=Tkinter.DISABLED)  

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

        if self._freeform_temp_line_id is not None:
            self._target_canvas.delete(self._freeform_temp_line_id)
        
        if self._radio_selection.get() == CURSOR:
            self._cursor_shape = None

        self._create_cursor_shape(event)

    def _create_cursor_shape(self, event):
        initial_size = 30
        aqt_scale = 2.5

        if self._radio_selection.get() == IMAGE:
            image = Image.open(self._image_path)
            self._cursor_photoimage = ImageTk.PhotoImage(image)

            self._cursor_shape = self._target_canvas.create_image(
                event.x, event.y, image=self._cursor_photoimage,
                tags=("_shape:image", "_path:" + self._image_path))

        elif self._radio_selection.get() == RECTANGLE:        
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

        elif self._radio_selection.get() == D_SILHOUETTE_3:        
            self._cursor_shape = self._target_canvas.create_polygon(
                event.x+15.083*aqt_scale,event.y+13.12*aqt_scale,
                event.x+15.083*aqt_scale,event.y+-0.147*aqt_scale,
                event.x+14.277*aqt_scale,event.y+-2.508*aqt_scale,
                event.x+13.149*aqt_scale,event.y+-4.115*aqt_scale,
                event.x+11.841*aqt_scale,event.y+-5.257*aqt_scale,
                event.x+10.557*aqt_scale,event.y+-6.064*aqt_scale,
                event.x+8.689*aqt_scale,event.y+-6.811*aqt_scale,
                event.x+7.539*aqt_scale,event.y+-8.439*aqt_scale,
                event.x+7.076*aqt_scale,event.y+-9.978*aqt_scale,
                event.x+6.104*aqt_scale,event.y+-11.577*aqt_scale,
                event.x+4.82*aqt_scale,event.y+-12.829*aqt_scale,
                event.x+3.43*aqt_scale,event.y+-13.788*aqt_scale,
                event.x+1.757*aqt_scale,event.y+-14.386*aqt_scale,
                event.x+0.083*aqt_scale,event.y+-14.55*aqt_scale,
                event.x+-1.59*aqt_scale,event.y+-14.386*aqt_scale,
                event.x+-3.263*aqt_scale,event.y+-13.788*aqt_scale,
                event.x+-4.653*aqt_scale,event.y+-12.829*aqt_scale,
                event.x+-5.938*aqt_scale,event.y+-11.577*aqt_scale,
                event.x+-6.909*aqt_scale,event.y+-9.978*aqt_scale,
                event.x+-7.372*aqt_scale,event.y+-8.439*aqt_scale,
                event.x+-8.522*aqt_scale,event.y+-6.811*aqt_scale,
                event.x+-10.39*aqt_scale,event.y+-6.064*aqt_scale,
                event.x+-11.674*aqt_scale,event.y+-5.257*aqt_scale,
                event.x+-12.982*aqt_scale,event.y+-4.115*aqt_scale,
                event.x+-14.11*aqt_scale,event.y+-2.508*aqt_scale,
                event.x+-14.917*aqt_scale,event.y+-0.147*aqt_scale,
                event.x+-14.917*aqt_scale,event.y+13.12*aqt_scale,
                fill="black", outline="black", stipple="gray25",
                tags=("_shape:aqt3"))

        elif self._radio_selection.get() == D_SILHOUETTE_4:        
            self._cursor_shape = self._target_canvas.create_polygon(
                event.x+11.66*aqt_scale,event.y+5.51*aqt_scale,
                event.x+11.595*aqt_scale,event.y+0.689*aqt_scale,
                event.x+11.1*aqt_scale,event.y+-1.084*aqt_scale,
                event.x+9.832*aqt_scale,event.y+-2.441*aqt_scale,
                event.x+7.677*aqt_scale,event.y+-3.322*aqt_scale,
                event.x+5.821*aqt_scale,event.y+-4.709*aqt_scale,
                event.x+4.715*aqt_scale,event.y+-6.497*aqt_scale,
                event.x+4.267*aqt_scale,event.y+-8.135*aqt_scale,
                event.x+3.669*aqt_scale,event.y+-9.41*aqt_scale,
                event.x+2.534*aqt_scale,event.y+-10.553*aqt_scale,
                event.x+1.436*aqt_scale,event.y+-11.091*aqt_scale,
                event.x+0.083*aqt_scale,event.y+-11.323*aqt_scale,
                event.x+-1.269*aqt_scale,event.y+-11.091*aqt_scale,
                event.x+-2.367*aqt_scale,event.y+-10.553*aqt_scale,
                event.x+-3.502*aqt_scale,event.y+-9.41*aqt_scale,
                event.x+-4.1*aqt_scale,event.y+-8.135*aqt_scale,
                event.x+-4.548*aqt_scale,event.y+-6.497*aqt_scale,
                event.x+-5.654*aqt_scale,event.y+-4.709*aqt_scale,
                event.x+-7.51*aqt_scale,event.y+-3.322*aqt_scale,
                event.x+-9.665*aqt_scale,event.y+-2.441*aqt_scale,
                event.x+-10.933*aqt_scale,event.y+-1.084*aqt_scale,
                event.x+-11.428*aqt_scale,event.y+0.689*aqt_scale,
                event.x+-11.493*aqt_scale,event.y+5.51*aqt_scale,
                fill="black", outline="black", stipple="gray25",
                tags=("_shape:aqt4"))
            
        elif self._radio_selection.get() == D_SILHOUETTE_5:        
            self._cursor_shape = self._target_canvas.create_polygon(
                event.x+7.893*aqt_scale,event.y+3.418*aqt_scale,
                event.x+7.893*aqt_scale,event.y+1.147*aqt_scale,
                event.x+7.255*aqt_scale,event.y+0.331*aqt_scale,
                event.x+5.622*aqt_scale,event.y+-0.247*aqt_scale,
                event.x+4.187*aqt_scale,event.y+-1.124*aqt_scale,
                event.x+2.833*aqt_scale,event.y+-2.339*aqt_scale,
                event.x+1.917*aqt_scale,event.y+-3.594*aqt_scale,
                event.x+1.219*aqt_scale,event.y+-5.048*aqt_scale,
                event.x+0.9*aqt_scale,event.y+-6.223*aqt_scale,
                event.x+0.801*aqt_scale,event.y+-7.1*aqt_scale,
                event.x+0.521*aqt_scale,event.y+-7.558*aqt_scale,
                event.x+0.083*aqt_scale,event.y+-7.617*aqt_scale,
                event.x+-0.354*aqt_scale,event.y+-7.558*aqt_scale,
                event.x+-0.634*aqt_scale,event.y+-7.1*aqt_scale,
                event.x+-0.733*aqt_scale,event.y+-6.223*aqt_scale,
                event.x+-1.052*aqt_scale,event.y+-5.048*aqt_scale,
                event.x+-1.75*aqt_scale,event.y+-3.594*aqt_scale,
                event.x+-2.666*aqt_scale,event.y+-2.339*aqt_scale,
                event.x+-4.02*aqt_scale,event.y+-1.124*aqt_scale,
                event.x+-5.455*aqt_scale,event.y+-0.247*aqt_scale,
                event.x+-7.088*aqt_scale,event.y+0.331*aqt_scale,
                event.x+-7.726*aqt_scale,event.y+1.147*aqt_scale,
                event.x+-7.726*aqt_scale,event.y+3.418*aqt_scale,
                fill="black", outline="black", stipple="gray25",
                tags=("_shape:aqt5"))

        elif self._radio_selection.get() == FREEFORM_POLYGON:     
            # draw a vertex for the polygon
            vertex_size = 2
   
            self._cursor_shape = self._target_canvas.create_oval(
                event.x - vertex_size,
                event.y - vertex_size,
                event.x + vertex_size,
                event.y + vertex_size, 
                fill="black", tags=("_shape:vertex"))

            # draw a dashed line between this vertex and the last
            # vertex drawn
            if len(self._freeform_vertices_points) > 0:
                last_point = self._freeform_vertices_points[-1]

                self._freeform_temp_line_id = self._target_canvas.create_line(
                    last_point,
                    event.x, event.y,
                    dash=(4,4), tags="_shape:freeform_edge")

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
        self._target_canvas.bind('<Control-z>', self.undo_vertex)
        self._target_canvas.bind('<ButtonPress-3>', self.canvas_right_click)

        self._canvas_manager = CanvasManager(self._target_canvas, self._image_regions_images)

        # Align this window with it's parent otherwise it ends up all kinds of
        # crazy places when multiple monitors are used
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()

        self._window.geometry("+%d+%d" % (parent_x+20, parent_y+20))

    def create_toolbar(self, parent):
       # Create the toolbar
        toolbar = Tkinter.Frame(parent, bd=1, relief=Tkinter.RAISED)
        self._radio_selection = Tkinter.IntVar()
        self._radio_selection.set(CURSOR)

        # Save button
        self._save_icon = Image.open("images/gnome_media_floppy.png")
        self.create_toolbar_button(toolbar, self._save_icon, 
            self.save_target, "Save Target")
        
        # cursor button
        self._cursor_icon = Image.open("images/cursor.png")
        self.create_radio_button(toolbar, self._cursor_icon, "Select Region", CURSOR)

        # image button
        self._image_icon = Image.open("images/gnome_image_x_generic.png")
        self.create_radio_button(toolbar, self._image_icon, "Draw Image", IMAGE)

        # rectangle button
        self._rectangle_icon = Image.open("images/rectangle.png")
        self.create_radio_button(toolbar, self._rectangle_icon, "Draw Rectangle", RECTANGLE)

        # oval button
        self._oval_icon = Image.open("images/oval.png")
        self.create_radio_button(toolbar, self._oval_icon, "Draw Oval", OVAL)

        # triangle button
        self._triangle_icon = Image.open("images/triangle.png")
        self.create_radio_button(toolbar, self._triangle_icon, "Draw Triangle", TRIANGLE)

        # Appleseed D Silhouette 3 button
        self._d_silhouette_3_icon = Image.open("images/appleseed_d_silhouette_3.png")
        self.create_radio_button(toolbar, self._d_silhouette_3_icon, "Draw D Silhouette 3", D_SILHOUETTE_3)

        # Appleseed D Silhouette 4 button
        self._d_silhouette_4_icon = Image.open("images/appleseed_d_silhouette_4.png")
        self.create_radio_button(toolbar, self._d_silhouette_4_icon, "Draw D Silhouette 4", D_SILHOUETTE_4)
        
        # Appleseed D Silhouette 5 button
        self._d_silhouette_5_icon = Image.open("images/appleseed_d_silhouette_5.png")
        self.create_radio_button(toolbar, self._d_silhouette_5_icon, "Draw D Silhouette 5", D_SILHOUETTE_5)

        # freeform polygon button
        self._freeform_polygon_icon = Image.open("images/freeform_polygon.png")
        self.create_radio_button(toolbar, self._freeform_polygon_icon, "Draw Freeform Polygon", FREEFORM_POLYGON)

        # bring forward button
        self._bring_forward_icon = Image.open("images/bring_forward.png")
        self.create_toolbar_button(toolbar, self._bring_forward_icon, 
            self.bring_forward, "Bring Forward")

        # send backward button
        self._send_backward_icon = Image.open("images/send_backward.png")
        self.create_toolbar_button(toolbar, self._send_backward_icon, 
            self.send_backward, "Send Backward")

        # show tags button
        tags_icon = ImageTk.PhotoImage(Image.open("images/tags.png"))  

        self._tag_popup_state = Tkinter.IntVar()
        self._tags_button = Tkinter.Checkbutton(toolbar,
            image=tags_icon, indicatoron=False, variable=self._tag_popup_state,
            command=self.toggle_tag_editor, state=Tkinter.DISABLED)
        self._tags_button.image = tags_icon
        self._tags_button.pack(side=Tkinter.LEFT, padx=2, pady=2)
        self.create_tooltip(self._tags_button, "Edit Selected Region's Tags")

        # color chooser
        self._fill_color_combo = ttk.Combobox(toolbar,
            values=["black", "blue", "green", "orange", "red", "white"],
            state="readonly")
        self._fill_color_combo.set("black")
        self._fill_color_combo.bind("<<ComboboxSelected>>", self.color_selected)
        self._fill_color_combo.configure(state=Tkinter.DISABLED)
        self._fill_color_combo.pack(side=Tkinter.LEFT, padx=2, pady=2)
        self.create_tooltip(self._fill_color_combo, "Set Selected Region's Fill Color")

        toolbar.pack(fill=Tkinter.X)

    def create_radio_button(self, parent, image, tooltip, selected_value):
        icon = ImageTk.PhotoImage(image)  

        button = Tkinter.Radiobutton(parent, image=icon,              
            indicatoron=False, variable=self._radio_selection,
            value=selected_value, command=self.radio_button_click)
        button.image = icon
        button.pack(side=Tkinter.LEFT, padx=2, pady=2)

        self.create_tooltip(button, tooltip)

    def create_toolbar_button(self, parent, image, command, tooltip, enabled=True):
        icon = ImageTk.PhotoImage(image)  

        button = Tkinter.Button(parent, image=icon, relief=Tkinter.RAISED, command=command)

        if not enabled:
            button.configure(state=Tkinter.DISABLED)

        button.image = icon
        button.pack(side=Tkinter.LEFT, padx=2, pady=2)

        self.create_tooltip(button, tooltip)

    def create_tooltip(self, widget, text):
        toolTip = ToolTip(widget)

        def enter(event):
            toolTip.showtip(text)

        def leave(event):
            toolTip.hidetip()

        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)

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
        self._freeform_vertices_points = []
        self._freeform_vertices_ids = []
        self._freeform_edges_ids = []
        self._freeform_temp_line_id = None
        self._image_regions_images = {}
        self.build_gui(parent, webcam_image)

        if target is not None:
            target_pickler = TargetPickler()
            (region_object, self._regions) = target_pickler.load(
                target, self._target_canvas, self._canvas_manager, 
                self._image_regions_images)

        self._notify_new_target = notifynewfunc

# From: http://www.voidspace.org.uk/python/weblog/arch_d7_2006_07_01.shtml

# This is used instead of Tix because we'd have to convert every widget in the
# editor to use Tix, but we some attributes (e.g. images) that aren't working right
# with Tix in Ubuntu 14.04
class ToolTip(object):
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        self.text = text
        if self.tipwindow or not self.text:
            return

        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 27
        y = y + cy + self.widget.winfo_rooty() +27
        self.tipwindow = tw = Tkinter.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))

        try:
            # For Mac OS
            tw.tk.call("::tk::unsupported::MacWindowStyle",
                       "style", tw._w,
                       "help", "noActivates")
        except Tkinter.TclError:
            pass

        label = Tkinter.Label(tw, text=self.text, justify=Tkinter.LEFT,
                      background="#ffffe0", relief=Tkinter.SOLID, borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()
