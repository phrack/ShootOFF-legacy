# Copyright (c) 2013 phrack. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import ConfigParser
import configurator
import os
import re
import Tkinter, ttk

DEFAULT_DETECTION_RATE = 100 #ms
DEFAULT_LASER_INTENSITY = 230
DEFAULT_MARKER_RADIUS = 2 #px
DEFAULT_IGNORE_LASER_COLOR = "none"
DEFAULT_USE_VIRTUAL_MAGAZINE = False
DEFAULT_VIRTUAL_MAGAZINE = 7
DEFAULT_USE_MALFUNCTIONS = False
DEFAULT_MALFUNCTION_PROBABILITY = 10.0

class PreferencesEditor():
    @staticmethod
    def map_configuration():
        config = ConfigParser.SafeConfigParser()
        config.read("settings.conf")
        preferences = {}    

        if os.path.exists("settings.conf"):
            try:
                preferences[configurator.DETECTION_RATE] = config.getint("ShootOFF",
                    configurator.DETECTION_RATE)
            except ConfigParser.NoOptionError:
                preferences[configurator.DETECTION_RATE] = DEFAULT_DETECTION_RATE

            try:
                preferences[configurator.LASER_INTENSITY] = config.getint("ShootOFF",
                    configurator.LASER_INTENSITY)
            except ConfigParser.NoOptionError:
                preferences[configurator.LASER_INTENSITY] = DEFAULT_LASER_INTENSITY

            try:
                preferences[configurator.MARKER_RADIUS] = config.getint("ShootOFF",
                    configurator.MARKER_RADIUS)
            except ConfigParser.NoOptionError:
                preferences[configurator.MARKER_RADIUS] = DEFAULT_MARKER_RADIUS

            try:
                preferences[configurator.IGNORE_LASER_COLOR] = config.get("ShootOFF",
                    configurator.IGNORE_LASER_COLOR)
            except ConfigParser.NoOptionError:
                preferences[configurator.IGNORE_LASER_COLOR] = DEFAULT_IGNORE_LASER_COLOR

            try:

                if (config.get("ShootOFF", configurator.USE_VIRTUAL_MAGAZINE).lower() == "true" or
                    config.get("ShootOFF", configurator.USE_VIRTUAL_MAGAZINE) == "1"):
                    preferences[configurator.USE_VIRTUAL_MAGAZINE] = True
                else:
                    preferences[configurator.USE_VIRTUAL_MAGAZINE] = False
            except ConfigParser.NoOptionError:
                preferences[configurator.USE_VIRTUAL_MAGAZINE] = DEFAULT_USE_VIRTUAL_MAGAZINE

            try:
                preferences[configurator.VIRTUAL_MAGAZINE] = config.getint("ShootOFF",
                    configurator.VIRTUAL_MAGAZINE)
            except ConfigParser.NoOptionError:
                preferences[configurator.VIRTUAL_MAGAZINE] = DEFAULT_VIRTUAL_MAGAZINE

            try:
                if (config.get("ShootOFF", configurator.USE_MALFUNCTIONS).lower() == "true" or
                    config.get("ShootOFF", configurator.USE_MALFUNCTIONS) == "1"):
                    preferences[configurator.USE_MALFUNCTIONS] = True
                else:
                    preferences[configurator.USE_MALFUNCTIONS] = False
            except ConfigParser.NoOptionError:
                preferences[configurator.USE_MALFUNCTIONS] = DEFAULT_USE_MALFUNCTIONS

            try:
                preferences[configurator.MALFUNCTION_PROBABILITY] = config.getfloat("ShootOFF",
                    configurator.MALFUNCTION_PROBABILITY)
            except ConfigParser.NoOptionError:
                preferences[configurator.MALFUNCTION_PROBABILITY] = DEFAULT_MALFUNCTION_PROBABILITY
        else:
            preferences[configurator.DETECTION_RATE] = DEFAULT_DETECTION_RATE
            preferences[configurator.LASER_INTENSITY] = DEFAULT_LASER_INTENSITY
            preferences[configurator.MARKER_RADIUS] = DEFAULT_MARKER_RADIUS
            preferences[configurator.IGNORE_LASER_COLOR] = DEFAULT_IGNORE_LASER_COLOR
            preferences[configurator.USE_VIRTUAL_MAGAZINE] = DEFAULT_USE_VIRTUAL_MAGAZINE
            preferences[configurator.VIRTUAL_MAGAZINE] = DEFAULT_VIRTUAL_MAGAZINE
            preferences[configurator.USE_MALFUNCTIONS] = DEFAULT_USE_MALFUNCTIONS
            preferences[configurator.MALFUNCTION_PROBABILITY] = DEFAULT_MALFUNCTION_PROBABILITY

            config.add_section("ShootOFF")
            config.set("ShootOFF", configurator.DETECTION_RATE, 
                str(preferences[configurator.DETECTION_RATE]))   
            config.set("ShootOFF", configurator.LASER_INTENSITY, 
                str(preferences[configurator.LASER_INTENSITY]))
            config.set("ShootOFF", configurator.MARKER_RADIUS, 
                str(preferences[configurator.MARKER_RADIUS]))
            config.set("ShootOFF", configurator.IGNORE_LASER_COLOR, 
                preferences[configurator.IGNORE_LASER_COLOR])  
            config.set("ShootOFF", configurator.USE_VIRTUAL_MAGAZINE, 
                str(preferences[configurator.USE_VIRTUAL_MAGAZINE]))  
            config.set("ShootOFF", configurator.VIRTUAL_MAGAZINE, 
                str(preferences[configurator.VIRTUAL_MAGAZINE]))  
            config.set("ShootOFF", configurator.USE_MALFUNCTIONS, 
                str(preferences[configurator.USE_MALFUNCTIONS]))  
            config.set("ShootOFF", configurator.MALFUNCTION_PROBABILITY, 
                str(preferences[configurator.MALFUNCTION_PROBABILITY]))      

            with open("settings.conf", "w") as config_file:
                config.write(config_file)

        return config, preferences

    def save_preferences(self):
        if self._detection_rate_spinbox.get():
            self._preferences[configurator.DETECTION_RATE] = int(
                self._detection_rate_spinbox.get())
        else:
            self._preferences[configurator.DETECTION_RATE] = DEFAULT_DETECTION_RATE

        if self._laser_intensity_spinbox.get():
            self._preferences[configurator.LASER_INTENSITY] = int(
                self._laser_intensity_spinbox.get())
        else:
            self._preferences[configurator.LASER_INTENSITY] = DEFAULT_LASER_INTENSITY

        if self._marker_radius_spinbox.get():
            self._preferences[configurator.MARKER_RADIUS] = int(
                self._marker_radius_spinbox.get())
        else:
            self._preferences[configurator.MARKER_RADIUS] = DEFAULT_MARKER_RADIUS

        if self._ignore_laser_color_combo.get():
            self._preferences[configurator.IGNORE_LASER_COLOR] = self._ignore_laser_color_combo.get()
        else:
            self._preferences[configurator.IGNORE_LASER_COLOR] = DEFAULT_IGNORE_LASER_COLOR

        self._preferences[configurator.USE_VIRTUAL_MAGAZINE] = self._virtual_magazine_state.get()
        if self._virtual_magazine_state.get() == True:
            if self._virtual_magazine_spinbox.get():
                self._preferences[configurator.VIRTUAL_MAGAZINE] = int(self._virtual_magazine_spinbox.get())
            else:
                self._preferences[configurator.VIRTUAL_MAGAZINE] = DEFAULT_VIRTUAL_MAGAZINE
         
        self._preferences[configurator.USE_MALFUNCTIONS] = self._malfunctions_state.get()
        if self._malfunctions_state.get() == True:
            if self._malfunction_probability_spinbox.get():
                self._preferences[configurator.MALFUNCTION_PROBABILITY] = float(self._malfunction_probability_spinbox.get())
            else:
                self._preferences[configurator.MALFUNCTION_PROBABILITY] = DEFAULT_MALFUNCTION_PROBABILITY

        self._config_parser.set("ShootOFF", configurator.DETECTION_RATE, 
            str(self._preferences[configurator.DETECTION_RATE]))
        self._config_parser.set("ShootOFF", configurator.LASER_INTENSITY,
            str(self._preferences[configurator.LASER_INTENSITY]))
        self._config_parser.set("ShootOFF", configurator.MARKER_RADIUS,
            str(self._preferences[configurator.MARKER_RADIUS]))
        self._config_parser.set("ShootOFF", configurator.IGNORE_LASER_COLOR,
            self._preferences[configurator.IGNORE_LASER_COLOR])
        self._config_parser.set("ShootOFF", configurator.USE_VIRTUAL_MAGAZINE,
             str(self._preferences[configurator.USE_VIRTUAL_MAGAZINE]))
        self._config_parser.set("ShootOFF", configurator.VIRTUAL_MAGAZINE,
             str(self._preferences[configurator.VIRTUAL_MAGAZINE]))
        self._config_parser.set("ShootOFF", configurator.USE_MALFUNCTIONS,
             str(self._preferences[configurator.USE_MALFUNCTIONS]))
        self._config_parser.set("ShootOFF", configurator.MALFUNCTION_PROBABILITY,
             str(self._preferences[configurator.MALFUNCTION_PROBABILITY]))

        with open("settings.conf", "w") as config_file:
            self._config_parser.write(config_file)

        self._window.destroy()

    def toggle_malfunctions(self):
        if self._malfunctions_state.get() == True :
            self._malfunction_probability_spinbox.configure(state=Tkinter.NORMAL)
        else:
            self._malfunction_probability_spinbox.configure(state=Tkinter.DISABLED)

    def toggle_virtual_magazine(self):
        if self._virtual_magazine_state.get() == True :
            self._virtual_magazine_spinbox.configure(state=Tkinter.NORMAL)
        else:
            self._virtual_magazine_spinbox.configure(state=Tkinter.DISABLED)

    def build_gui(self, parent):
        self._window = Tkinter.Toplevel(parent)
        self._window.transient(parent)
        self._window.title("Preferences")

        self._frame = ttk.Frame(self._window)
        self._frame.pack(padx=15, pady=15)

        ttk.Label(self._frame, 
            text="Detection Rate (ms): ").grid(column=0, row=0)

        self._detection_rate_spinbox = Tkinter.Spinbox(self._frame, from_=1,
            to=60000)
        self._detection_rate_spinbox.delete(0, Tkinter.END)
        self._detection_rate_spinbox.insert(0, 
            self._preferences[configurator.DETECTION_RATE])
        rate_validator = (self._window.register(self.check_detection_rate),'%P')
        self._detection_rate_spinbox.config(validate="key",
            validatecommand=rate_validator)
        self._detection_rate_spinbox.grid(column=1, row=0)

        ttk.Label(self._frame, 
            text="Laser Intensity: ").grid(column=0, row=1)

        self._laser_intensity_spinbox = Tkinter.Spinbox(self._frame, from_=1,
            to=255)
        self._laser_intensity_spinbox.delete(0, Tkinter.END)
        self._laser_intensity_spinbox.insert(0, 
            self._preferences[configurator.LASER_INTENSITY])
        intensity_validator = (self._window.register(self.check_laser_intensity),
            '%P')
        self._laser_intensity_spinbox.config(validate="key",
            validatecommand=intensity_validator)
        self._laser_intensity_spinbox.grid(column=1, row=1)

        ttk.Label(self._frame, 
            text="Marker Radius: ").grid(column=0, row=2)

        self._marker_radius_spinbox = Tkinter.Spinbox(self._frame, from_=1,
            to=20)  
        self._marker_radius_spinbox.delete(0, Tkinter.END)
        self._marker_radius_spinbox.insert(0, 
            self._preferences[configurator.MARKER_RADIUS])
        radius_validator = (self._window.register(self.check_marker_radius),'%P')
        self._marker_radius_spinbox.config(validate="key",
            validatecommand=radius_validator)
        self._marker_radius_spinbox.grid(column=1, row=2)  

        ttk.Label(self._frame, 
            text="Ignore Laser Color: ").grid(column=0, row=3)

        self._ignore_laser_color_combo = ttk.Combobox(self._frame, values=["none", "red", "green"],
            state="readonly")
        self._ignore_laser_color_combo.set(self._preferences[configurator.IGNORE_LASER_COLOR])
        self._ignore_laser_color_combo.grid(column=1, row=3)

        self._virtual_magazine_state = Tkinter.BooleanVar()
        self._virtual_magazine_state.set(self._preferences[configurator.USE_VIRTUAL_MAGAZINE])   

        self._use_virtual_magazine_button = Tkinter.Checkbutton(self._frame,
            variable=self._virtual_magazine_state, text="Virtual Magazine",
            onvalue=True, offvalue=False,
            command=self.toggle_virtual_magazine).grid(column=0, row=4)

        self._virtual_magazine_spinbox = Tkinter.Spinbox(self._frame, from_=1,
            to=45)  
        self._virtual_magazine_spinbox.delete(0, Tkinter.END)
        self._virtual_magazine_spinbox.insert(0, 
            self._preferences[configurator.VIRTUAL_MAGAZINE])
        virtual_magazine_validator = (self._window.register(self.check_virtual_magazine),'%P')
        self._virtual_magazine_spinbox.config(validate="key",
            validatecommand=virtual_magazine_validator)
        self._virtual_magazine_spinbox.grid(column=1, row=4)  
        self.toggle_virtual_magazine()

        self._malfunctions_state = Tkinter.BooleanVar()
        self._malfunctions_state.set(self._preferences[configurator.USE_MALFUNCTIONS])   

        self._use_malfunctions_button = Tkinter.Checkbutton(self._frame,
            variable=self._malfunctions_state, text="Inject Malfunctions (%)",
            onvalue=True, offvalue=False,
            command=self.toggle_malfunctions).grid(column=0, row=5)

        self._malfunction_probability_spinbox = Tkinter.Spinbox(self._frame, from_=.1,
            to=99.9, increment=0.1, format="%0.1f")  
        self._malfunction_probability_spinbox.delete(0, Tkinter.END)
        self._malfunction_probability_spinbox.insert(0, 
            self._preferences[configurator.MALFUNCTION_PROBABILITY])
        malfunction_probability_validator = (self._window.register(self.check_malfunction_probability),'%P')
        self._malfunction_probability_spinbox.config(validate="key",
            validatecommand=malfunction_probability_validator)
        self._malfunction_probability_spinbox.grid(column=1, row=5)  
        self.toggle_malfunctions()

        self._ok_button = ttk.Button(self._frame, text="OK",
            command=self.save_preferences, width=10)
        self._ok_button.grid(column=0, row=6)
        self._cancel_button = ttk.Button(self._frame, text="Cancel",
            command=self._window.destroy, width=10)
        self._cancel_button.grid(column=1, row=6)

        # Center this window on its parent
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()

        self_width = self._window.winfo_width()
        self_height = self._window.winfo_height()

        self._window.geometry("+%d+%d" % (parent_x+(parent_width - self_width)/4,
            parent_y+(parent_height-self_height)/4))

        self._frame.pack()

    def check_detection_rate(self, P):
        if (P.isdigit() and int(P) > 0) or not P:
            return True
        else:
            return False

    def check_laser_intensity(self, P):
        if (P.isdigit() and int(P) > 0 and int(P) <= 255) or not P:
            return True
        else:
            return False

    def check_marker_radius(self, P):
        if (P.isdigit() and int(P) >= 1 and int(P) <= 20) or not P:
            return True
        else:
            return False

    def check_virtual_magazine(self, P):
        if (P.isdigit() and int(P) >= 1 and int(P) <= 45) or not P:
            return True
        else:
            return False

    def check_malfunction_probability(self, P):
        try:
            r = re.compile("^[\d\.]+$")
            if (r.match(P) and float(P) >= 0.1 and float(P) <= 99.9) or not P:
                return True
            else:
                return False
        except ValueError:
            return True

    def __init__(self, parent, config_parser, preferences):
        self._config_parser = config_parser
        self._preferences = preferences

        self.build_gui(parent)
