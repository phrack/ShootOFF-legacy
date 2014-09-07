# Copyright (c) 2013 phrack. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import Tkinter, tkMessageBox, ttk

class TimerIntervalWindow():
    def _ok_click(self):
        min_val = int(self._min_spinbox.get())
        max_val = int(self._max_spinbox.get())

        if (max_val <= min_val):
            tkMessageBox.showerror("Bad Delay Interval", "Max must be greater than min.")
            return

        self._notify_interval(min_val, max_val)     
        self._window.destroy()   

    def build_gui(self, parent):
        # Create the main window
        self._window = Tkinter.Toplevel(parent)
        self._window.protocol("WM_DELETE_WINDOW", self._ok_click)
        self._window.transient(parent)
        self._window.title("Delayed Start Interval")

        # Controls
        min_label = Tkinter.Label(self._window, text="Min (s)") 
        min_label.grid(row=0, column=0)
        self._min_spinbox = Tkinter.Spinbox(self._window, from_=1, to=300)
        self._min_spinbox.delete(0, "end")
        self._min_spinbox.insert(0, 4)
        interval_validator = (self._window.register(self.check_interval),'%P')
        self._min_spinbox.config(validate="key", validatecommand=interval_validator)

        self._min_spinbox.grid(row=0, column=1)   

        max_label = Tkinter.Label(self._window, text="Max (s)")	
        max_label.grid(row=1, column=0)
        self._max_spinbox = Tkinter.Spinbox(self._window, from_=1, to=300)
        self._max_spinbox.delete(0, "end")
        self._max_spinbox.insert(0, 8)
        self._max_spinbox.config(validate="key", validatecommand=interval_validator)
        self._max_spinbox.grid(row=1, column=1)

        ok_button = Tkinter.Button(self._window, text="OK", command=self._ok_click)
        ok_button.grid(row=2, columnspan=2)

        # Align this window with it's parent otherwise it ends up all kinds of
        # crazy places when multiple monitors are used
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()

        self._window.geometry("+%d+%d" % (parent_x+20, parent_y+20))

    def check_interval(self, P):
        if (P.isdigit() and int(P) > 0 and int(P) <= 300) or not P:
            return True
        else:
            return False

    def __init__(self, parent, notifyinterval=None):
		self.build_gui(parent)
		self._notify_interval = notifyinterval
