# Copyright (c) 2013 phrack. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import pyaudio
import pyttsx
from threading import Thread
from training_protocols.timer_interval_window import TimerIntervalWindow
import wave

LARGEST_REGION = 0
BOUNDING_BOX = 1

SAMPWIDTH_INDEX = 0
NCHANNELS_INDEX = 1
FRAMERATE_INDEX = 2
DATA_INDEX = 3

# This class hold shootoff functions that should be exposed to training protocol
# plugins. Each instance of a plugin has its own instance of this class.
class ProtocolOperations():
    def __init__(self, canvas, shootoff):
        self._canvas = canvas
        self._plugin_canvas_artifacts = []
        self._shootoff = shootoff
        self._feed_text = self._canvas.create_text(1, 1, anchor="nw", fill="white")
        self._plugin_canvas_artifacts.append(self._feed_text)
        self._added_columns = ()
        self._added_column_widths = []
        self._sound_cache = {}

        self._tts_engine = pyttsx.init()
        # slow down the wpm rate otherwise they speek to fast
        self._tts_engine.setProperty("rate", 150)
        self._tts_engine.startLoop(False)

    # Shows a popup window that lets the user set the interval for a random start 
    # delay in seconds. Notify interval points to a function that gets the min
    # and max values for the interval as parameters.
    def get_delayed_start_interval(self, parent, notifyinterval=None):
        tiw = TimerIntervalWindow(parent, notifyinterval)
        parent.wait_window(tiw._window)

    # Returns the centroid of a target using the specified mode:
    # LARGEST_REGION calculates the centroid of the target by calculating
    #   the centroid of the largest region. The largest region is determined
    #   by calculating the area of the each region's bounding box (this isn't as
    #   accurate as determining the area of each region, but it's simple). This
    #   mode works well for targets with stacked regions (e.g. a traditional bullseye).
    # BOUNDING_BOX calculates the centroid of a target by calculating the center of 
    #   the bounding box that encompasses all of a target's region. This mode works
    #   well for targets whose regions are not stacked (e.g. a target with 5 separate
    #   bullseyes). 
    def calculate_target_centroid(self, target, mode=LARGEST_REGION):
        coords = ()
        target_name = "_internal_name" + ":" + target["regions"][0]["_internal_name"]
        
        if mode == LARGEST_REGION:
            regions = self._canvas.find_withtag(target_name)
            largest_region = None

            # Find the largest region by bounding box size
            for region in regions:
                if largest_region is None:
                    largest_region = region
                elif self._area_bbox(largest_region) < self._area_bbox(region):
                    largest_region = region

            coords = self._canvas.coords(largest_region)

        elif mode == BOUNDING_BOX:
            coords = self._canvas.bbox(target_name)

        # Calculate centroid
        x = coords[::2]
        y = coords[1::2]
        return (sum(x) / len(x), sum(y) / len(x))

    # This method expects to get the id of a target region on a canvas and will return
    # the area of its bounding box
    def _area_bbox(self, region):
        coords = self._canvas.bbox(region)
        width = coords[2] - coords[0]
        height = coords[3] - coords[1]
        return (width * height)

    # new_columns is a tuple containing the names of the new columns to added
    # widths is a list of each column's width in pixels. 
    # it must be true that len(new_columns) == len(column_sizes)
    def add_shot_list_columns(self, new_columns, widths):
        self._added_columns += new_columns
        if len(self._added_column_widths) == 0:
            self._added_column_widths = widths
        else:
            self._added_column_widths += widths 

        self._shootoff.add_shot_list_columns(new_columns)
        self._shootoff.configure_default_shot_list_columns()
        self._shootoff.configure_shot_list_columns(self._added_columns,
            self._added_column_widths)               

    # appends the tuple values the value tuple that already exists for item.
    # This is how data is added by a training protocol to columns it added.
    def append_shot_item_values(self, item, values):
        self._shootoff.append_shot_list_column_data(item, values)

    def destroy(self):
        # pyttsx errors out if we try to end a loop that isn't running, so
        # we need to check if we are in a loop first, but the only good
        # way to do this right now is to check an internal flag. This hack
        # checks that the flag exists and checks it before ending the loop
        # if it does, otherwise we just end the loop (better to get a CLI
        # error message than the actual behavior of not ending the loop,
        # which is weird sound artifacts).
        if hasattr(self._tts_engine, "_inLoop") and self._tts_engine._inLoop:
            self._tts_engine.endLoop()
        elif not hasattr(self._tts_engine, "_inLoop"):
            self._tts_engine.endLoop()
        self.clear_canvas()
        self.clear_protocol_shot_list_columns()
        self.pause_shot_detection(False)

    # If pause is set to true hit's won't register. If pause is set to false
    # hits will register.
    def pause_shot_detection(self, pause):
        self._shootoff.pause_shot_detection(pause)

    # This clears shots without resetting the current protocol (it is
    # identical to clicking the clear shots button aside from the protocol's
    # reset method being called)
    def clear_shots(self):
        self._shootoff.clear_shots()

    # This performs the same operation as hitting the reset button
    def reset(self):
        self._shootoff.reset_click()

    # Use text-to-speech to say message outloud
    def say(self, message):
        # if we don't do this on another thread we have to wait until
        # the message has finished being communicated to do anything
        # (i.e. shootoff freezes)  
        self._say_thread = Thread(target=self._say, args=(message,),
                name="say_thread")
        self._say_thread.start()  
    
    def _say(self, *args):
        self._tts_engine.say(args[0])
        if hasattr(self._tts_engine, "_inLoop") and self._tts_engine._inLoop:
            self._tts_engine.iterate()

    # Show message as text on the top left corner of the webcam feed. The 
    # new message will over-write whatever was shown before
    def show_text_on_feed(self, message):
        self._canvas.itemconfig(self._feed_text, text=message)

    # Remove anything added by the plugin from the canvas
    def clear_canvas(self):
        for artifact in self._plugin_canvas_artifacts:
            self._canvas.delete(artifact)

    # Removes all traces of shot list columns/data added by the plugin
    def clear_protocol_shot_list_columns(self):
        self._shootoff.revert_shot_list_columns()

    def _cache_sound(self):
        wavs = glob.glob("sounds/*.wav")
        
        for wav in wavs:
            self._add_wav_cache(wav)

    # Returns true of the projector arena is open, false otherwise
    def projector_arena_visible(self):
        return self._shootoff.get_projector_arena().is_visible()

    # Adds a target to the projector arena where name is the name of the .target file to use
    # (e.g. targets/ISSF.target) and x, y is the location of the top left corner
    # of the target
    def add_projector_target(self, name, x, y):
        arena = self._shootoff.get_projector_arena()
        target_name = arena.add_target_loc(name, x, y);

        return target_name

    def delete_projector_target(self, target_name):
        arena = self._shootoff.get_projector_arena()
        arena.delete_target(target_name);
    
    def get_target_name(self, region):
        for tag in self._arena_canvas.gettags(region):
            if tag.startswith("_internal_name:"):
                return tag

    # Returns a (width, height) tuple for the projector arena's canvas
    def get_projector_arena_dimensions(self):
        arena = self._shootoff.get_projector_arena()
        return arena.get_arena_dimensions()

    # Play the sound in sound_files
    def play_sound(self, sound_file):
        # if we don't do this on a nother thread we have to wait until
        # the message has finished being communicated to do anything
        # (i.e. shootoff freezes)  
        self._play_sound_thread = Thread(target=self._play_sound, 
            args=(sound_file,), name="play_sound_thread")
        self._play_sound_thread.start()  

    def _play_sound(self, *args):
        sound_file = args[0]  
        if sound_file not in self._sound_cache:
            self._add_wav_cache(sound_file)

        # initialize the sound file and stream  
        p = pyaudio.PyAudio()  
        stream = p.open(format = p.get_format_from_width(self._sound_cache[sound_file][SAMPWIDTH_INDEX]),  
                        channels = self._sound_cache[sound_file][NCHANNELS_INDEX],  
                        rate = self._sound_cache[sound_file][FRAMERATE_INDEX],
                        output = True)  

        # play the sound file
        for data in self._sound_cache[sound_file][DATA_INDEX]:
            stream.write(data) 

        # clean up
        stream.stop_stream()  
        stream.close()  
        p.terminate() 

    def _add_wav_cache(self, sound_file):
        chunk = 1024
        
        f = wave.open(sound_file,"rb")
        
        self._sound_cache[sound_file] = (f.getsampwidth(), f.getnchannels(), 
            f.getframerate(), [])

        data = f.readframes(chunk)   
        while data != '':  
            self._sound_cache[sound_file][DATA_INDEX].append(data)
            data = f.readframes(chunk) 
