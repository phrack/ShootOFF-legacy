# Copyright (c) 2013 phrack. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import pyttsx
from threading import Thread

# This class hold shootoff functions that should be exposed to training protocol
# plugins. Each instance of a plugin has its own instance of this class.
class ProtocolOperations():
    def __init__(self, canvas):
        self._canvas = canvas
        self._plugin_canvas_artifacts = []
        self._feed_text = self._canvas.create_text(1, 1, anchor="nw")
        self._plugin_canvas_artifacts.append(self._feed_text)

        self._tts_engine = pyttsx.init()
        # slow down the wpm rate otherwise they speek to fast
        self._tts_engine.setProperty("rate", 150)
        self._tts_engine.startLoop(False)

    # Use text-to-speech to say message outloud
    def say(self, message):
        # if we don't do this on a nother thread we have to wait until
        # the message has finished being communicated to do anything
        # (i.e. shootoff freezes)  
        self._say_thread = Thread(target=self._say, args=(message,),
                name="say_thread")
        self._say_thread.start()  
    
    def _say(self, *args):
        self._tts_engine.say(args[0])
        self._tts_engine.iterate()

    # Show message as text on the top left corner of the webcam feed. The 
    # new message will over-write whatever was shown before
    def show_text_on_feed(self, message):
        self._canvas.itemconfig(self._feed_text, text=message)

    # Remove anything added by the plugin from the canvas
    def clear_canvas(self):
        for artifact in self._plugin_canvas_artifacts:
            self._canvas.delete(artifact)

