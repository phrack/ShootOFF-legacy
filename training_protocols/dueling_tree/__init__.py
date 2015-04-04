# Copyright (c) 2015 phrack. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import threading
from training_protocols.ITrainingProtocol import ITrainingProtocol 

class DuelingTree(ITrainingProtocol):
    def __init__(self, main_window, protocol_operations, targets):
        self._operations = protocol_operations

        # We need to make sure we start with a clean slate because the position
        # of the plates matter
        self._operations.reset()
        
        self._continue_protocol = True
        self._protocol_is_resetting = False
        self._left_score = 0
        self._right_score = 0
        self._targets_on_left = []
        self._targets_on_right = []

        self._wait_event = threading.Event()

        if self._find_targets(targets):
            self._operations.add_shot_list_columns(("Hit By",), [45])

    def _find_targets(self, targets):
        found_target = False

        # Find the first target with directional subtargets and gets its regions
        for target in targets:
            if found_target:
                break

            for region in target["regions"]:
                if "subtarget" in region:
                    if region["subtarget"].startswith("left_plate"):
                        self._targets_on_left.append(region["subtarget"])
                        found_target = True
                    elif region["subtarget"].startswith("right_plate"):
                        self._targets_on_right.append(region["subtarget"])
                        found_target = True

        if not found_target:
            self._operations.say("This training protocol requires a dueling tree target")
        else:
            self._operations.show_text_on_feed("left score: 0\nright score: 0")

        return found_target

    def shot_listener(self, shot, shot_list_item, is_hit):
        return

    def hit_listener(self, region, tags, shot, shot_list_item):
        if "subtarget" in tags:
            if (tags["subtarget"].startswith("left_plate") or tags["subtarget"].startswith("right_plate")):
                if tags["subtarget"] in self._targets_on_left:
                    self._targets_on_left.remove(tags["subtarget"])
                    self._targets_on_right.append(tags["subtarget"])
                    hit_by = "left"
                elif tags["subtarget"] in self._targets_on_right:   
                    self._targets_on_left.append(tags["subtarget"])                                     
                    self._targets_on_right.remove(tags["subtarget"])
                    hit_by = "right"

                self._operations.append_shot_item_values(shot_list_item,
                    (hit_by,))

            if (len(self._targets_on_right) == 6):
                self._left_score += 1
                self._round_over()
               
            if (len(self._targets_on_left) == 6):
                self._right_score += 1
                self._round_over()

    def _round_over(self):
        message = "left score: %d\nright score: %d" % (self._left_score, 
                    self._right_score)

        self._operations.show_text_on_feed(message)
        if self._continue_protocol:        
            self._operations.pause_shot_detection(True)

            self._new_round_thread = Thread(target=self._new_round,
                                              name="new_round_thread")
            self._new_round_thread.start()

    def _new_round(self):
        # Wait five seconds before starting another round
        self._wait_event.wait(5)

        self._protocol_is_resetting = True
        self._operations.reset()
        self._protocol_is_resetting = False
        self._operations.pause_shot_detection(False)

        message = "left score: %d\nright score: %d" % (self._left_score, 
                    self._right_score)

        self._operations.show_text_on_feed(message)

    def reset(self, targets):
        if not self._protocol_is_resetting:
            self._left_score = 0
            self._right_score = 0
            self._operations.show_text_on_feed("left score: 0\nright score: 0")
            self._protocol_is_resetting = False

        self._targets_on_left = []
        self._targets_on_right = []

        self._find_targets(targets)

    def destroy(self):
        self._continue_protocol = False
        self._wait_event.set()
        pass

def get_info():
    protocol_info = {}

    protocol_info["name"] = "Dueling Tree"
    protocol_info["version"] = "1.0"
    protocol_info["creator"] = "phrack"
    desc = "This protocol works with the dueling tree target. Challenge " 
    desc += "a friend, assign a side (left or right) to each participant, "
    desc += "and try to shoot the plates from your side to your friend's "
    desc += "side. A round ends when all plates are on one person's side. "
    protocol_info["description"] = desc

    return protocol_info

def load(main_window, protocol_operations, targets):
    return DuelingTree(main_window, protocol_operations, targets)
