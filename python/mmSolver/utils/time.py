# Copyright (C) 2019 David Cattermole.
#
# This file is part of mmSolver.
#
# mmSolver is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# mmSolver is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with mmSolver.  If not, see <https://www.gnu.org/licenses/>.
#
"""
Time related utilities.
"""


import maya.cmds


def get_maya_timeline_range_inner():
    """
    Get the Maya frame range (inner bar).

    :returns: start frame and end frame as tuple.
    :rtype: int, int
    """
    s = maya.cmds.playbackOptions(query=True, minTime=True)
    e = maya.cmds.playbackOptions(query=True, maxTime=True)
    return int(s), int(e)


def get_maya_timeline_range_outer():
    """
    Get the Maya frame range (outer bar).

    :returns: start frame and end frame as tuple.
    :rtype: int, int
    """
    s = maya.cmds.playbackOptions(query=True, animationStartTime=True)
    e = maya.cmds.playbackOptions(query=True, animationEndTime=True)
    return int(s), int(e)

