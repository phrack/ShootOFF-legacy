# Copyright (c) 2015 phrack. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import random
import threading
from training_protocols.ITrainingProtocol import ITrainingProtocol 

class ShootDontShoot(ITrainingProtocol):
    def __init__(self, main_window, protocol_operations, targets):
        self._operations = protocol_operations

        self._operations.clear_shots()

        self._continue_protocol = True
        self._arena_dimensions = self._operations.get_projector_arena_dimensions()
        self._missed_targets = 0
        self._bad_hits = 0
        self._current_shoot_targets = []
        self._current_dont_shoot_targets = []
        self._wait_event = threading.Event()

        self._operations.add_shot_list_columns(("Target",), [60])

        if not self._operations.projector_arena_visible():
            self._operations.say("This protocol only works on the projector arena.")
        else:
            self._add_targets(self._current_shoot_targets, "training_protocols/shoot_dont_shoot/shoot.target")
            self._add_targets(self._current_dont_shoot_targets, "training_protocols/shoot_dont_shoot/dont_shoot.target")  
            self._operations.show_text_on_feed("missed targets: 0\nbad hits: 0")      

            self._new_round_thread = Thread(target=self._new_round,
                                          name="new_round_thread")
            self._new_round_thread.start()

    def _add_targets(self, target_list, name):
        # Put up between zero and three targets
        target_count = random.randrange(0, 4)

        for i in range(0, target_count):
            x = random.randrange(0, self._arena_dimensions[0] - 100)
            y = random.randrange(0, self._arena_dimensions[1] - 100)

            target_list.append(self._operations.add_projector_target(name, x, y))

    def shot_listener(self, shot, shot_list_item, is_hit):
        return

    def hit_listener(self, region, tags, shot, shot_list_item):
        if "subtarget" in tags:
            target_name = self._operations.get_target_name(region)

            if tags["subtarget"] == "shoot":
                self._remove_target(target_name)
                self._current_shoot_targets.remove(target_name)
                self._operations.append_shot_item_values(shot_list_item,
                    (tags["subtarget"],))
            elif tags["subtarget"] == "dont_shoot":
                self._remove_target(target_name)
                self._current_dont_shoot_targets.remove(target_name)
                self._bad_hits += 1
                self._operations.append_shot_item_values(shot_list_item,
                    (tags["subtarget"],))
                self._operations.say("Bad shoot!")
                
    def _new_round(self):
        # Wait ten seconds before starting another round
        self._wait_event.wait(10)

        if self._continue_protocol:
            missed = len(self._current_shoot_targets)
            self._missed_targets += missed
            if missed > 0:
                self._operations.say("You missed " + str(missed) + " shoot targets.")

            self._operations.clear_shots()

            message = "missed targets: %d\nbad hits: %d" % (self._missed_targets, self._bad_hits)
            self._operations.show_text_on_feed(message)

            self._remove_old_targets(self._current_shoot_targets)
            self._current_shoot_targets = []
            self._remove_old_targets(self._current_dont_shoot_targets)
            self._current_dont_shoot_targets = [] 

            self._add_targets(self._current_shoot_targets, "training_protocols/shoot_dont_shoot/shoot.target")
            self._add_targets(self._current_dont_shoot_targets, "training_protocols/shoot_dont_shoot/dont_shoot.target")  

        if self._continue_protocol:
            self._new_round()

    def _remove_target(self, target_name):
        self._operations.delete_projector_target(target_name)

    def _remove_old_targets(self, target_list):
        for target in target_list:
            self._remove_target(target)

    def reset(self, targets):
        self._missed_targets = 0
        self._bad_hits = 0

        if not self._operations.projector_arena_visible():
            self._operations.say("This protocol only works on the projector arena.")
        else:
            self._remove_old_targets(self._current_shoot_targets)
            self._current_shoot_targets = []
            self._remove_old_targets(self._current_dont_shoot_targets)
            self._current_dont_shoot_targets = []

            self._add_targets(self._current_shoot_targets, "training_protocols/shoot_dont_shoot/shoot.target")
            self._add_targets(self._current_dont_shoot_targets, "training_protocols/shoot_dont_shoot/dont_shoot.target")  

            message = "missed targets: %d\nbad hits: %d" % (self._missed_targets, self._bad_hits)
            self._operations.show_text_on_feed(message)

            self._new_round_thread = Thread(target=self._new_round,
                                          name="new_round_thread")
            self._new_round_thread.start()


    def destroy(self):
        self._continue_protocol = False
        self._wait_event.set()
        self._remove_old_targets(self._current_shoot_targets)
        self._remove_old_targets(self._current_dont_shoot_targets) 
        
def get_info():
    protocol_info = {}

    protocol_info["name"] = "Shoot Don't Shoot"
    protocol_info["version"] = "1.0"
    protocol_info["creator"] = "phrack"
    desc = "This protocol randomly puts up targets and gives you 10 seconds" 
    desc += "to decide which ones to shoot and which ones to ignore. If "
    desc += "you do not shoot a target you are supposed to shoot, it gets "
    desc += "added to your missed targets counter and the protocol says "
    desc += "how many targets you missed. If you hit a target you were not "
    desc += "supposed to hit, the protocol says 'bad shoot!'. Shoot the targets "
    desc += "with the red ring, don't shoot the other targets."
    protocol_info["description"] = desc

    return protocol_info

def load(main_window, protocol_operations, targets):
    return ShootDontShoot(main_window, protocol_operations, targets)
