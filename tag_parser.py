# Copyright (c) 2013 phrack. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

class TagParser():
    @staticmethod
    def parse_tags(tag_list):
        tags = {}

        for tag in tag_list:
            if ":" not in tag: continue
            (prop, value) = tag.split(":", 1)

            # if the property name is command we need 
            # to make a list of commands            
            if prop == "command":
                if "command" not in tags:
                    tags[prop] = []

                tags[prop].append(value)
            else:            
                tags[prop] = value

        return tags
