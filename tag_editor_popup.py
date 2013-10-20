# Copyright (c) 2013 phrack. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import Tkinter, tkMessageBox

class TagEditorPopup():
    def _add_tag(self, event):
        tag = event.widget.get()

        if tag.count(":") != 1:
            tkMessageBox.showerror("Invalid Property",
                "\"" + tag + 
                "\" is not a valid property. It must be in the form: name:value",
                parent=self._parent)
            return

        self._tags_listbox.insert(Tkinter.END, tag)
        event.widget.delete(0, Tkinter.END)

        self._tag_change_listener(self._tags_listbox.get(0, Tkinter.END))

    def _delete_tag(self, event):
        event.widget.delete(event.widget.curselection())

        self._tag_change_listener(event.widget.get(0, Tkinter.END))

    def hide(self):
        self._tags_entry.pack_forget()
        self._tags_listbox.pack_forget()
        self._tags_popup.pack_forget()
        self._tags_popup.place_forget()

    def show(self, tags, x, y):
        self._tags_entry.delete(0, Tkinter.END)
        self._tags_listbox.delete(0, Tkinter.END)

        for tag in tags:
            # tags that start with _ are internal and should not be
            # modified by the user
            if not tag.startswith("_"):
                self._tags_listbox.insert(Tkinter.END, tag)

        self._tags_entry.pack()
        self._tags_listbox.pack()
        self._tags_popup.pack()

        self._tags_popup.place(x=x, y=y)  

    def __init__(self, parent, tag_change_listener):
        # Layout popup controls
        self._tags_popup = Tkinter.Frame(parent)        
        self._tags_entry = Tkinter.Entry(self._tags_popup)
        self._tags_entry.bind('<Return>', self._add_tag)
        self._tags_listbox = Tkinter.Listbox(self._tags_popup)  
        self._tags_listbox.bind('<Delete>', self._delete_tag)

        self._tag_change_listener = tag_change_listener
        self._parent = parent
