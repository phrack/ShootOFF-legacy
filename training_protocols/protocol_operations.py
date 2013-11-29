# Copyright (c) 2013 phrack. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import pyaudio
import pyttsx
from threading import Thread
import wave

# This class hold shootoff functions that should be exposed to training protocol
# plugins. Each instance of a plugin has its own instance of this class.
class ProtocolOperations():
    def __init__(self, canvas, shootoff):
        self._canvas = canvas
        self._plugin_canvas_artifacts = []
        self._shootoff = shootoff
        self._feed_text = self._canvas.create_text(1, 1, anchor="nw", fill="white")
        self._plugin_canvas_artifacts.append(self._feed_text)

        self._tts_engine = pyttsx.init()
        # slow down the wpm rate otherwise they speek to fast
        self._tts_engine.setProperty("rate", 150)
        self._tts_engine.startLoop(False)

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

    def clear_shots(self):
        self._shootoff.clear_shots()

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
        self._tts_engine.iterate()

    # Show message as text on the top left corner of the webcam feed. The 
    # new message will over-write whatever was shown before
    def show_text_on_feed(self, message):
        self._canvas.itemconfig(self._feed_text, text=message)

    # Remove anything added by the plugin from the canvas
    def clear_canvas(self):
        for artifact in self._plugin_canvas_artifacts:
            self._canvas.delete(artifact)

    # Play the sound in sound_file
    def play_sound(self, sound_file):
        # if we don't do this on a nother thread we have to wait until
        # the message has finished being communicated to do anything
        # (i.e. shootoff freezes)  
        self._play_sound_thread = Thread(target=self._play_sound, 
            args=(sound_file,), name="play_sound_thread")
        self._play_sound_thread.start()  

    def _play_sound(self, *args):
        chunk = 1024  
  
        # initialize the sound file and stream
        f = wave.open(args[0],"rb")  
        p = pyaudio.PyAudio()  
        stream = p.open(format = p.get_format_from_width(f.getsampwidth()),  
                        channels = f.getnchannels(),  
                        rate = f.getframerate(),  
                        output = True)  

        # play the sound file
        data = f.readframes(chunk)   
        while data != '':  
            stream.write(data)  
            data = f.readframes(chunk)  

        # clean up
        stream.stop_stream()  
        stream.close()  
        p.terminate() 
