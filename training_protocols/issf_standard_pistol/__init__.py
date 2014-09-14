# Copyright (c) 2013 phrack. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import random
import threading
from threading import Thread
from training_protocols.ITrainingProtocol import ITrainingProtocol

class ISSFStandardPistol(ITrainingProtocol):
    def __init__(self, main_window, protocol_operations, targets):
        self._operations = protocol_operations

        self._operations.add_shot_list_columns(("Score", "Round"), [45, 70])        
        self._operations.pause_shot_detection(True)
        
        self._continue_protocol = True
        self._round_times = [150, 20, 10]
        self._round_time_index = 0
        self._round = 1    
        self._shot_count = 0
        self._running_score = 0
        self._session_scores = {}

        for _time in self._round_times:
            self._session_scores[_time] = 0

        self._parent = main_window
        self._operations.get_delayed_start_interval(self._parent, self.update_interval)

        self._wait_event = threading.Event()
        self._event_ended = threading.Event()

        self._setup_wait = Thread(target=self.setup_wait,
                                          name="setup_wait_thread")
        self._setup_wait.start()

    def update_interval(self, new_min, new_max):
        self._interval_min = new_min
        self._interval_max = new_max

    def setup_wait(self):
        # Give the shooter 10 seconds to position themselves
        self._wait_event.wait(10)

        if self._continue_protocol:
            self._start_round = Thread(target=self.start_round,
                                          name="start_round_thread")
            self._start_round.start()

    def start_round(self):        
        self._shot_count = 0
        self._operations.say("Shooter... make ready")

        random_delay = random.randrange(self._interval_min, self._interval_max)
        self._wait_event.wait(random_delay)
        
        if self._continue_protocol:
            self._operations.play_sound("sounds/beep.wav")
            self._operations.pause_shot_detection(False)
            self._wait_event.wait(self._round_times[self._round_time_index])
            self._operations.pause_shot_detection(True)
           
        if self._continue_protocol:
            self._operations.say("Round over")

            if (self._round < 4):
                # Go to next round
                self._round += 1
                self.start_round()
            elif (self._round_time_index < len(self._round_times) - 1):
                # Go to round 1 for next time
                self._round = 1
                self._round_time_index += 1
                self.start_round()
            else:
                self._operations.say("Event over... Your score is " + str(self._running_score))
                # At this point we end and the user has to hit clear shots to start again

        if not self._continue_protocol:
            self._event_ended.set()
                
    def shot_listener(self, shot, shot_list_item, is_hit):
        self._shot_count += 1
        
        if (self._shot_count == 5): 
            # Round is over due to shot maximum
            self._wait_event.set()
            self._wait_event.clear()

        if (not is_hit):
            hit_score = 0
            current_round = "R" + str(self._round) + " (" + \
                    str(self._round_times[self._round_time_index]) + "s)"        
            self._operations.append_shot_item_values(shot_list_item,
                    (hit_score, current_round))

    def hit_listener(self, region, tags, shot, shot_list_item):
        if "points" in tags:
            hit_score = int(tags["points"])

            self._session_scores[self._round_times[self._round_time_index]] += hit_score

            self._running_score += hit_score

            message = ""
    
            for _time in self._round_times:
                message += "%ss score: %d\n" % (_time, self._session_scores[_time])

            self._operations.show_text_on_feed(message + "total score: " + str(self._running_score))

            current_round = "R" + str(self._round) + " (" + \
                str(self._round_times[self._round_time_index]) + "s)"       
 
            self._operations.append_shot_item_values(shot_list_item,
                (hit_score, current_round))

    def reset(self, targets): 
        self._continue_protocol = False  
        self._wait_event.set()
       
        self._round_time_index = 0
        self._round = 1    
        self._shot_count = 0
        self._running_score = 0

        for _time in self._round_times:
            self._session_scores[_time] = 0
     
        self._operations.show_text_on_feed("")

        self._event_ended.wait(1)
        self._event_ended.clear()

        self._continue_protocol = True
        self._wait_event.clear()

        self._setup_wait = Thread(target=self.setup_wait,
                                          name="setup_wait_thread")
        self._setup_wait.start()

    def destroy(self):
        self._continue_protocol = False
        self._wait_event.set()

def get_info():
    protocol_info = {}

    protocol_info["name"] = "ISSF 25M Standard Pistol"
    protocol_info["version"] = "1.0"
    protocol_info["creator"] = "phrack"
    desc = "This protocol implements the ISSF event describe at: " 
    desc += "http://www.pistol.org.au/events/disciplines/issf. You "
    desc += "can use any scored target with this protocol, but use "
    desc += "the ISSF target for the most authentic experience."
    protocol_info["description"] = desc

    return protocol_info

def load(main_window, protocol_operations, targets):
    return ISSFStandardPistol(main_window, protocol_operations, targets)
