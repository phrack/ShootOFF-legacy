# Copyright (c) 2013 phrack. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

class ITrainingProtocol():
    def __init__(self, protocol_operations, targets):
        # Called when the training protocol is loaded. Initialize the training
        # protocol here.
        pass

    def shot_listener(self, shot, is_hit):
        # Called whenever a shot is detected. The shot may not have hit
        # a target: is_hit will be False for a miss or True for a hit 
        pass

    def hit_listener(self, region, tags):
        # Called whenever a shot is detected that hit a target. Region is
        # the region that was hit and tags is a dictionary containing
        # all of region's tags in value = tags["tag_name"].
	pass

    def reset(self):
        # Reset the training protocols state to it's initial state.
        pass

    def destroy(self):
        # Called when a training protocol is being unloaded by the framework
        pass

def get_info():
    protocol_info = {}

    protocol_info["name"] = "ITrainingProtocol"
    protocol_info["version"] = "1.0"
    protocol_info["creator"] = "phrack"
    desc = "The required interface for all training protocol plugins."
    protocol_info["description"] = desc

    return protocol_info

def load(protocol_operations, targets):
    return ITrainingProtocol(protocol_operations, targets)
