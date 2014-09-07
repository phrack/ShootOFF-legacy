# Copyright (c) 2013 phrack. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import random
import threading
from threading import Thread
import time
from training_protocols.ITrainingProtocol import ITrainingProtocol 

class TimedHolsterDrill(ITrainingProtocol):
    def __init__(self, main_window, protocol_operations, targets):
        self._operations = protocol_operations

        self._operations.add_shot_list_columns(("Length",), [60])
    
        # TODO: Get interval for random delayed start instead of hardcoding it
        self._interval_min = 4
        self._interval_max = 8

        self._wait_event = threading.Event()

        self._setup_wait = Thread(target=self.setup_wait,
                                          name="setup_wait_thread")
        self._setup_wait.start()

    def setup_wait(self):
        # Give the shooter 10 seconds to position themselves
        self._wait_event.wait(10)
        self._operations.say("Shooter... make ready")

        self._repeat_protocol = True
        self._random_delay = Thread(target=self.random_delay,
                                          name="random_delay_thread")
        self._random_delay.start()

    def random_delay(self):
        random_delay = random.randrange(self._interval_min, self._interval_max)
        self._wait_event.wait(random_delay)

        if (self._repeat_protocol):
            self._operations.play_sound("sounds/beep.wav")
            self._beep_time = time.time()
            self.random_delay()

    def shot_listener(self, shot, shot_list_item, is_hit):
        # Calculate difference between beep time and current time and
        # add it to the list
        draw_shot_length = time.time() - self._beep_time
        self._operations.append_shot_item_values(shot_list_item, (draw_shot_length,))

        pass

    def hit_listener(self, region, tags, shot, shot_list_item):
        pass

    def reset(self, targets):
        # TODO: Ask for the interval again
        self._repeat_protocol = False

    def destroy(self):
        self._repeat_protocol = False

def get_info():
    protocol_info = {}

    protocol_info["name"] = "Timed Holster Drill"
    protocol_info["version"] = "1.0"
    protocol_info["creator"] = "phrack"
    desc = "This protocol does not require a target, but one may be used " 
    desc += "to give the shooter something to shoot at. When the protocol "
    desc += "is started you are asked to enter a range for randomly "
    desc += "delayed starts. You are then given 10 seconds to position "
    desc += "yourself. After a random wait (within the entered range) a "
    desc += "beep tells you to draw their pistol from it's holster, "
    desc += "fire at your target, and finally re-holster. This process is "
    desc += "repeated as long as this protocol is on."
    protocol_info["description"] = desc

    return protocol_info

def load(main_window, protocol_operations, targets):
    return TimedHolsterDrill(main_window, protocol_operations, targets)
