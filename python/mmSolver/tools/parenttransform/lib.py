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
Mimic the parent and unparent tool in Maya.

.. todo:: Unlike the native Maya parent/unparent tools, this tool will
   maintain the world-space position for all keyframes across time.
"""

import maya.cmds

import mmSolver.logger

import mmSolver.utils.node as node_utils
import mmSolver.utils.time as time_utils
import mmSolver.utils.animcurve as anim_utils
import mmSolver.utils.transform as tfm_utils

import mmSolver.api as mmapi

LOG = mmSolver.logger.get_logger()

TRANSLATE_ATTRS = [
    'translateX', 'translateY', 'translateZ',
]

ROTATE_ATTRS = [
    'rotateX', 'rotateY', 'rotateZ',
]

SCALE_ATTRS = [
    'scaleX', 'scaleY', 'scaleZ',
]

TFM_ATTRS = []
TFM_ATTRS += TRANSLATE_ATTRS
TFM_ATTRS += ROTATE_ATTRS
TFM_ATTRS += SCALE_ATTRS


def parent(src_nodes, dst_node):
    """
    Parent selected nodes under the last selected node.
    """
    assert len(src_nodes) > 0
    assert len(dst_node) > 0
    src_tfm_nodes = [tfm_utils.TransformNode(node=n)
                     for n in src_nodes]
    tfm_dst_node = tfm_utils.TransformNode(node=dst_node)

    # TODO: Get time values to query.

    # # Create Transform Cache, add and process cache.
    # times = []
    # cache = tfm_utils.TransformMatrixCache()
    # for tfm_src_node in src_tfm_nodes:
    #     src_node = tfm_src_node.get_node()
    #     cache.add_node(src_node, times)
    # cache.process()

    # Re-parent the nodes.
    dst_node = tfm_dst_node.get_node()
    src_nodes = [tfm_node.get_node()
                 for tfm_node in src_tfm_nodes]
    maya.cmds.parent(src_nodes, dst_node, relative=True)

    # TODO: Set transforms for all source nodes.

    src_nodes = [tfm_node.get_node()
                 for tfm_node in src_tfm_nodes]
    return src_nodes


def unparent(src_nodes):
    """
    Un-parent selected nodes into world space.
    """
    assert len(src_nodes) > 0
    src_tfm_nodes = [tfm_utils.TransformNode(node=n)
                     for n in src_nodes]

    # TODO: Store the transforms for the given nodes.

    # Perform the re-parent operation
    src_nodes = [tfm_node.get_node()
                 for tfm_node in src_tfm_nodes]
    maya.cmds.parent(src_nodes, world=True, relative=True)

    # TODO: Set transforms for all source nodes.

    src_nodes = [tfm_node.get_node()
                 for tfm_node in src_tfm_nodes]
    return src_nodes
