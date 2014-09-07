# Copyright (c) 2013 phrack. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import random
from training_protocols.ITrainingProtocol import ITrainingProtocol 

class RandomShoot(ITrainingProtocol):
    def __init__(self, main_window, protocol_operations, targets):
        self._operations = protocol_operations
        self._subtarget_chain = None
        self._subtargets = []

        if self.find_supported_target(targets):
            self.pick_subtargets()
            self.say_subtargets()       

    def find_supported_target(self, targets): 
        found_target = False

        # Find the first target with subtargets and gets its regions
        for target in targets:
            if found_target:
                break

            for region in target["regions"]:
                if "subtarget" in region:
                    self._subtargets.append(region["subtarget"])
                    found_target = True

        if found_target and len(self._subtargets) > 0:
            return True
        else:
            self._operations.say("This training protocol requires a target with subtargets")
            return False

    def pick_subtargets(self):
        # We want to choose a random number of subtargets from the chain
        # then pick that number of subtargets at random
        chain_length = random.randrange(1, len(self._subtargets))

        self._subtarget_chain = []	
        for i in range(0, chain_length):
            self._subtarget_chain.append(random.choice(self._subtargets))

        self._subtarget_index = 0

    def say_subtargets(self):
        # Create a string for the targets to say then say it using TTS
        sentence = "shoot subtarget %s " % self._subtarget_chain[0]

        for subtarget in self._subtarget_chain[1:]:
            sentence += "then %s " % subtarget

        self._operations.say(sentence.strip())

    def say_current_subtarget(self):
        self._operations.say("shoot %s" % 
            self._subtarget_chain[self._subtarget_index])

    def shot_listener(self, shot, shot_list_item, is_hit):
        if not self._subtarget_chain:
            return

        if not is_hit:
            self.say_current_subtarget()

        return

    def hit_listener(self, region, tags, shot, shot_list_item):
        if not self._subtarget_chain:
            return

        if "subtarget" in tags and tags["subtarget"] == self._subtarget_chain[self._subtarget_index]:
            self._subtarget_index += 1

            if self._subtarget_index == len(self._subtarget_chain):
                self.pick_subtargets()
                self.say_subtargets()
        else:
            self.say_current_subtarget()

    def reset(self, targets):
        if self.find_supported_target(targets):
            self.pick_subtargets()
            self.say_subtargets()

    def destroy(self):
        pass

def get_info():
    protocol_info = {}

    protocol_info["name"] = "Random Shoot"
    protocol_info["version"] = "1.0"
    protocol_info["creator"] = "phrack"
    desc = "This protocol works with targets that have subtarget tags " 
    desc += "assigned to some regions. Subtargets are selected at random "
    desc += "and the shooter is asked to shoot those subtargets in order. "
    desc += "If a subtarget is shot out of order or the shooter misses, the "
    desc += "name of the subtarget that should have been shot is repeated."
    protocol_info["description"] = desc

    return protocol_info

def load(main_window, protocol_operations, targets):
    return RandomShoot(main_window, protocol_operations, targets)
