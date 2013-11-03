# Copyright (c) 2013 phrack. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import ConfigParser
import os
import Tkinter

DETECTION_RATE = "detectionrate"
LASER_INTENSITY = "laserintensity"
MARKER_RADIUS = "markerradius"
IGNORE_LASER_COLOR = "ignorelasercolor"

DEFAULT_DETECTION_RATE = 100 #ms
DEFAULT_LASER_INTENSITY = 230
DEFAULT_MARKER_RADIUS = 2 #px
DEFAULT_IGNORE_LASER_COLOR = "none"

class PreferencesEditor():
    @staticmethod
    def map_configuration():
        config = ConfigParser.SafeConfigParser()
        config.read("settings.conf")
        preferences = {}    

        if os.path.exists("settings.conf"):
            try:
                preferences[DETECTION_RATE] = config.getint("ShootOFF",
                    DETECTION_RATE)
            except ConfigParser.NoOptionError:
                preferences[DETECTION_RATE] = DEFAULT_DETECTION_RATE

            try:
                preferences[LASER_INTENSITY] = config.getint("ShootOFF",
                    LASER_INTENSITY)
            except ConfigParser.NoOptionError:
                preferences[LASER_INTENSITY] = DEFAULT_LASER_INTENSITY

            try:
                preferences[MARKER_RADIUS] = config.getint("ShootOFF", MARKER_RADIUS)
            except ConfigParser.NoOptionError:
                preferences[MARKER_RADIUS] = DEFAULT_MARKER_RADIUS

            try:
                preferences[IGNORE_LASER_COLOR] = config.get("ShootOFF",
                    IGNORE_LASER_COLOR)
            except ConfigParser.NoOptionError:
                preferences[IGNORE_LASER_COLOR] = DEFAULT_IGNORE_LASER_COLOR
        else:
            preferences[DETECTION_RATE] = DEFAULT_DETECTION_RATE
            preferences[LASER_INTENSITY] = DEFAULT_LASER_INTENSITY
            preferences[MARKER_RADIUS] = DEFAULT_MARKER_RADIUS
            preferences[IGNORE_LASER_COLOR] = DEFAULT_IGNORE_LASER_COLOR

            config.add_section("ShootOFF")
            config.set("ShootOFF", DETECTION_RATE, 
                str(preferences[DETECTION_RATE]))   
            config.set("ShootOFF", LASER_INTENSITY, 
                str(preferences[LASER_INTENSITY]))
            config.set("ShootOFF", MARKER_RADIUS, 
                str(preferences[MARKER_RADIUS]))
            config.set("ShootOFF", IGNORE_LASER_COLOR, 
                preferences[IGNORE_LASER_COLOR])    

            with open("settings.conf", "w") as config_file:
                config.write(config_file)

        return config, preferences

    def save_preferences(self):
        if self._detection_rate_spinbox.get():
            self._preferences[DETECTION_RATE] = int(
                self._detection_rate_spinbox.get())
        else:
            self._preferences[DETECTION_RATE] = DEFAULT_DETECTION_RATE

        if self._laser_intensity_spinbox.get():
            self._preferences[LASER_INTENSITY] = int(
                self._laser_intensity_spinbox.get())
        else:
            self._preferences[LASER_INTENSITY] = DEFAULT_LASER_INTENSITY

        if self._marker_radius_spinbox.get():
            self._preferences[MARKER_RADIUS] = int(
                self._marker_radius_spinbox.get())
        else:
            self._preferences[MARKER_RADIUS] = DEFAULT_MARKER_RADIUS

        if self._ignore_laser_color.get():
            self._preferences[IGNORE_LASER_COLOR] = self._ignore_laser_color.get()
        else:
            self._preferences[IGNORE_LASER_COLOR] = DEFAULT_IGNORE_LASER_COLOR

        self._config.set("ShootOFF", DETECTION_RATE, 
            str(self._preferences[DETECTION_RATE]))
        self._config.set("ShootOFF", LASER_INTENSITY,
            str(self._preferences[LASER_INTENSITY]))
        self._config.set("ShootOFF", MARKER_RADIUS,
            str(self._preferences[MARKER_RADIUS]))
        self._config.set("ShootOFF", IGNORE_LASER_COLOR,
            self._preferences[IGNORE_LASER_COLOR])

        with open("settings.conf", "w") as config_file:
            self._config.write(config_file)

        self._window.destroy()

    def build_gui(self, parent):
        self._window = Tkinter.Toplevel(parent)
        self._window.transient(parent)
        self._window.title("Preferences")

        self._frame = Tkinter.Frame(self._window)
        self._frame.pack(padx=15, pady=15)

        Tkinter.Label(self._frame, 
            text="Detection Rate (ms): ").grid(column=0, row=0)

        self._detection_rate_spinbox = Tkinter.Spinbox(self._frame, from_=1,
            to=60000)
        self._detection_rate_spinbox.delete(0, Tkinter.END)
        self._detection_rate_spinbox.insert(0, 
            self._preferences[DETECTION_RATE])
        rate_validator = (self._window.register(self.check_detection_rate),'%P')
        self._detection_rate_spinbox.config(validate="key",
            validatecommand=rate_validator)
        self._detection_rate_spinbox.grid(column=1, row=0)

        Tkinter.Label(self._frame, 
            text="Laser Intensity: ").grid(column=0, row=1)

        self._laser_intensity_spinbox = Tkinter.Spinbox(self._frame, from_=0,
            to=255)
        self._laser_intensity_spinbox.delete(0, Tkinter.END)
        self._laser_intensity_spinbox.insert(0, 
            self._preferences[LASER_INTENSITY])
        intensity_validator = (self._window.register(self.check_laser_intensity),
            '%P')
        self._laser_intensity_spinbox.config(validate="key",
            validatecommand=intensity_validator)
        self._laser_intensity_spinbox.grid(column=1, row=1)

        Tkinter.Label(self._frame, 
            text="Marker Radius: ").grid(column=0, row=2)

        self._marker_radius_spinbox = Tkinter.Spinbox(self._frame, from_=1,
            to=20)  
        self._marker_radius_spinbox.delete(0, Tkinter.END)
        self._marker_radius_spinbox.insert(0, 
            self._preferences[MARKER_RADIUS])
        radius_validator = (self._window.register(self.check_marker_radius),'%P')
        self._marker_radius_spinbox.config(validate="key",
            validatecommand=radius_validator)
        self._marker_radius_spinbox.grid(column=1, row=2)  

        Tkinter.Label(self._frame, 
            text="Ignore Laser Color: ").grid(column=0, row=3)

        self._ignore_laser_color = Tkinter.StringVar()
        self._ignore_laser_color.set(self._preferences[IGNORE_LASER_COLOR])
        self._ignore_laser_color_menu = Tkinter.OptionMenu(self._frame,
            self._ignore_laser_color, "none", "red", "green")
        self._ignore_laser_color_menu.grid(column=1, row=3)

        self._ok_button = Tkinter.Button(self._frame, text="OK",
            command=self.save_preferences, width=10)
        self._ok_button.grid(column=0, row=4)
        self._cancel_button = Tkinter.Button(self._frame, text="Cancel",
            command=self._window.destroy, width=10)
        self._cancel_button.grid(column=1, row=4)

        self._frame.pack()

    def check_detection_rate(self, P):
        if (P.isdigit() and int(P) > 0) or not P:
            return True
        else:
            return False

    def check_laser_intensity(self, P):
        if (P.isdigit() and int(P) >= 0 and int(P) <= 255) or not P:
            return True
        else:
            return False

    def check_marker_radius(self, P):
        if (P.isdigit() and int(P) >= 1 and int(P) <= 20) or not P:
            return True
        else:
            return False

    def __init__(self, parent, config, preferences):
        self._config = config
        self._preferences = preferences

        self.build_gui(parent)
