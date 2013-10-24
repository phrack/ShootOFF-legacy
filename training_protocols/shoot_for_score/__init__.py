# Copyright (c) 2013 phrack. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from training_protocols.ITrainingProtocol import ITrainingProtocol 

class ShootForScore(ITrainingProtocol):
    def __init__(self, protocol_operations, targets):
	self._operations = protocol_operations
        self._score = 0

    def shot_listener(self, shot, is_hit):
        return

    def hit_listener(self, region, tags):
        if "points" in tags:
            self._score += int(tags["points"])
            self._operations.show_text_on_feed("score: " + str(self._score))

    def reset(self):
        self._score = 0
	self._operations.show_text_on_feed("score: 0")

    def destroy(self):
        pass

def get_info():
    protocol_info = {}

    protocol_info["name"] = "Shoot for Score"
    protocol_info["version"] = "1.0"
    protocol_info["creator"] = "phrack"
    desc = "This protocol works with targets that have score tags " 
    desc += "assigned to regions. Any time a target region is hit, "
    desc += "the number of points assigned to that region are added "
    desc += "to your total score."
    protocol_info["description"] = desc

    return protocol_info

def load(protocol_operations, targets):
    return ShootForScore(protocol_operations, targets)
