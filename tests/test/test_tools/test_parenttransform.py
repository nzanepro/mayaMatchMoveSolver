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
Test functions for parenttransform tool.
"""

import unittest

import maya.cmds
import maya.debug.closeness as closeness

import test.test_tools.toolsutils as test_tools_utils
import mmSolver.tools.parenttransform.lib as lib


# @unittest.skip
class TestParentTransform(test_tools_utils.ToolsTestCase):

    def create_no_keyframe_scene(self):
        tfm_a = maya.cmds.createNode('transform')
        tfm_b = maya.cmds.createNode('transform', parent=tfm_a)
        maya.cmds.setAttr(tfm_b + '.translateX', 10.0)
        maya.cmds.setAttr(tfm_b + '.translateY', 20.0)
        maya.cmds.setAttr(tfm_b + '.translateZ', 30.0)
        tfm_c = maya.cmds.createNode('transform')
        return tfm_a, tfm_b, tfm_c

    def test_one(self):
        tfm_a, tfm_b, tfm_c = self.create_no_keyframe_scene()
        ctrls = lib.parent([tfm_a, tfm_b], tfm_c)
        ctrl_a, ctrl_b = ctrls

        maya.cmds.setAttr(ctrl_b + '.ty', 42.0)

        nodes = lib.unparent([ctrl_a, ctrl_b])

        # save the output
        path = self.get_data_path('parenttransform_one_after.ma')
        maya.cmds.file(rename=path)
        maya.cmds.file(save=True, type='mayaAscii', force=True)

        node = nodes[0]
        self.assertEqual(maya.cmds.getAttr(node + '.translateX'), 10.0)
        self.assertEqual(maya.cmds.getAttr(node + '.translateY'), 42.0)
        self.assertEqual(maya.cmds.getAttr(node + '.translateZ'), 30.0)
        return


if __name__ == '__main__':
    prog = unittest.main()
