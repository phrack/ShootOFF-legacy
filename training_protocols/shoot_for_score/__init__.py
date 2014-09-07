# Copyright (c) 2013 phrack. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from training_protocols.ITrainingProtocol import ITrainingProtocol 

class ShootForScore(ITrainingProtocol):
    def __init__(self, main_window, protocol_operations, targets):
        self._operations = protocol_operations
        self._red_score = 0
        self._green_score = 0

        self._operations.add_shot_list_columns(("Score",), [40])

    def shot_listener(self, shot, shot_list_item, is_hit):
        return

    def hit_listener(self, region, tags, shot, shot_list_item):
        if "points" in tags:
            if "red" in shot.get_color():
                self._red_score += int(tags["points"])
            elif "green" in shot.get_color():
                self._green_score += int(tags["points"])

            message = "score: 0"

            if self._red_score > 0 and self._green_score > 0:
                message = "red score: %d\ngreen score: %d" % (self._red_score, 
                    self._green_score)
            elif self._red_score > 0:
                message = "red score: %d" % self._red_score
            elif self._green_score > 0:
                message = "green score: %d" % self._green_score

            self._operations.append_shot_item_values(shot_list_item,
                (int(tags["points"]),))
            self._operations.show_text_on_feed(message)

    def reset(self, targets):
        self._red_score = 0
        self._green_score = 0
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

def load(main_window, protocol_operations, targets):
    return ShootForScore(main_window, protocol_operations, targets)
