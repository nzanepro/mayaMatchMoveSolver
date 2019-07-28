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
Create a controller transform node.

Ideas::

  - Have a flag to allow maintaining the relative hierarchy of the
    input transforms.

.. note:: If no keyframes are set, this tool works on the current
   frame and adds a keyframe to the controller.

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
    'translateX', 'translateY', 'translateZ'
]

ROTATE_ATTRS = [
    'rotateX', 'rotateY', 'rotateZ'
]

SCALE_ATTRS = [
    'scaleX', 'scaleY', 'scaleZ'
]

TFM_ATTRS = []
TFM_ATTRS += TRANSLATE_ATTRS
TFM_ATTRS += ROTATE_ATTRS
TFM_ATTRS += SCALE_ATTRS


def _get_keyable_attrs(node, attrs):
    keyable_attrs = set()
    for attr in attrs:
        plug = node + '.' + attr
        keyable = maya.cmds.getAttr(plug, keyable=True)
        settable = maya.cmds.getAttr(plug, settable=True)
        if settable is True and keyable is True:
            keyable_attrs.add(plug)
    return keyable_attrs


def _get_skip_attrs(node, attrs):
    assert len(attrs) == 3
    axis_list = ['x', 'y', 'z']
    skip_attrs = set(axis_list)
    for axis, attr in zip(axis_list, attrs):
        plug = node + '.' + attr
        keyable = maya.cmds.getAttr(plug, keyable=True)
        settable = maya.cmds.getAttr(plug, settable=True)
        if settable is True and keyable is True:
            skip_attrs.remove(axis)
    return skip_attrs


def _get_constraints_from_ctrls(input_node):
    """
    Get Constraints 'input_node' is connected to.
    """
    constraints = maya.cmds.listConnections(
        input_node,
        type='constraint',
        source=False,
        destination=True) or []
    constraints = [n for n in constraints
                   if node_utils.node_is_referenced(n) is False]
    constraints = set(constraints)
    if len(constraints) == 0:
        LOG.warn('node is not controlling anything: %r', input_node)
        return set()
    return constraints


def _get_destination_nodes_from_ctrls(constraints):
    """
    Get nodes connected to constraints.
    """
    dest_nodes = set()
    attr = 'constraintParentInverseMatrix'
    for constraint in constraints:
        plug = constraint + '.' + attr
        temp = maya.cmds.listConnections(
            plug,
            type='transform',
            source=True,
            destination=False,
        ) or []
        dest_nodes |= set(temp)
    if len(dest_nodes) != 1:
        return []
    return list(dest_nodes)


def _create_constraint(src_node, dst_node):
    constraints = []
    skip = _get_skip_attrs(src_node, TRANSLATE_ATTRS)
    if len(skip) != 3:
        constraints += maya.cmds.pointConstraint(
            dst_node,
            src_node,
            skip=tuple(skip)
        )
    skip = _get_skip_attrs(src_node, ROTATE_ATTRS)
    if len(skip) != 3:
        constraints += maya.cmds.orientConstraint(
            dst_node,
            src_node,
            skip=tuple(skip)
        )
    skip = _get_skip_attrs(src_node, SCALE_ATTRS)
    if len(skip) != 3:
        constraints += maya.cmds.scaleConstraint(
            dst_node,
            src_node,
            skip=tuple(skip)
        )
    return


def create(nodes,
           current_frame=None,
           eval_mode=None):
    """
    Create controllers for each given node.

    If the node has no keyframes on the attributes, keyframe
    the attributes on the current frame number (or allow the user
    to specify the frame). This will make the tool more predicable
    for the user.
    
    .. todo:: Copy animation curve pre/post infinity values to new
       animation curves.

    :param nodes: The nodes to operate on.
    :type nodes: [str, ..]

    :param current_frame: What frame number is considered to be
                          'current' when evaluating transforms without
                          any keyframes.
    :type current_frame: float or int

    :param eval_mode: What type of transform evaluation method to use?
    :type eval_mode: mmSolver.utils.constant.EVAL_MODE_*

    :returns: List of created controller transform nodes.
    :rtype: [str, ..]
    """
    if current_frame is None:
        current_frame = maya.cmds.currentTime(query=True)
    assert current_frame is not None

    tfm_nodes = [tfm_utils.TransformNode(node=n)
                 for n in nodes]
    nodes = [n.get_node() for n in tfm_nodes]

    # Query keyframe times on each node attribute
    key_times_map = time_utils.get_keyframe_times_for_node_attrs(nodes, TFM_ATTRS)

    # Query the transform matrix for the nodes
    cache = tfm_utils.TransformMatrixCache()
    for tfm_node in tfm_nodes:
        node = tfm_node.get_node()
        times = key_times_map.get(node, [current_frame])
        cache.add_node(tfm_node, times)
    cache.process(eval_mode=eval_mode)

    # TODO: Sort transform nodes by hierarchy depth; level 0 first, 1
    # second, until 'n'.

    # TODO: For each transform node, get the parent transform above
    # it. If no parent node exists, get the parent should be None (ie,
    # world or root).

    # Create new (locator) node for each input node
    ctrl_list = []
    for tfm_node in tfm_nodes:
        node = tfm_node.get_node()
        name = node.rpartition('|')[-1]
        assert '|' not in name
        name = name.replace(':', '_')
        name = name + '_CTRL'
        name = mmapi.find_valid_maya_node_name(name)
        # TODO: Allow maintaining relative hierarchy of nodes.
        tfm = maya.cmds.createNode('transform', name=name)
        maya.cmds.createNode('locator', parent=tfm)
        rot_order = maya.cmds.xform(node, query=True, rotateOrder=True)
        maya.cmds.xform(tfm, rotateOrder=rot_order, preserve=True)
        ctrl_list.append(tfm)
    ctrl_tfm_nodes = [tfm_utils.TransformNode(node=tfm)
                      for tfm in ctrl_list]

    # Set transform matrix on new node
    anim_curves = []
    for src, dst in zip(tfm_nodes, ctrl_tfm_nodes):
        src_node = src.get_node()
        src_times = key_times_map.get(src_node, [current_frame])
        assert len(src_times) > 0
        tfm_utils.set_transform_values(
            cache, src_times, src, dst,
            delete_static_anim_curves=False
        )
        src_had_keys = key_times_map.get(src_node) is not None
        if src_had_keys is True:
            continue
        # Maintain that destination node will not have keyframes now, the
        # same as the source node.
        dst_node = dst.get_node()
        keyable_attrs = _get_keyable_attrs(dst_node, TFM_ATTRS)
        anim_curves += anim_utils.get_anim_curves_from_nodes(
            list(keyable_attrs),
        )
    anim_curves = [n for n in anim_curves
                   if node_utils.node_is_referenced(n) is False]
    if len(anim_curves) > 0:
        maya.cmds.delete(anim_curves)

    # Delete all keyframes on controlled nodes
    keyable_attrs = set()
    for tfm_node in tfm_nodes:
        node = tfm_node.get_node()
        keyable_attrs |= _get_keyable_attrs(node, TFM_ATTRS)
    anim_curves = anim_utils.get_anim_curves_from_nodes(
        list(keyable_attrs),
    )
    anim_curves = [n for n in anim_curves
                   if node_utils.node_is_referenced(n) is False]
    if len(anim_curves) > 0:
        maya.cmds.delete(anim_curves)

    # Create constraint(s) to previous nodes.
    for tfm_node, ctrl in zip(tfm_nodes, ctrl_tfm_nodes):
        src_node = tfm_node.get_node()
        dst_node = ctrl.get_node()
        _create_constraint(src_node, dst_node)
    return ctrl_list


def remove(nodes,
           current_frame=None,
           eval_mode=None):
    """
    Remove a controller and push the animation back to the controlled
    object.

    .. todo:: Order the nodes to remove by hierarchy depth. This means
       that children will be removed first, then parents, this ensures
       we don't delete a controller accidentally when a parent
       controller is deleted first.

    :param nodes: The nodes to operate on.
    :type nodes: [str, ..]

    :param current_frame: What frame number is considered to be
                          'current' when evaluating transforms without
                          any keyframes.
    :type current_frame: float or int

    :param eval_mode: What type of transform evaluation method to use?
    :type eval_mode: mmSolver.utils.constant.EVAL_MODE_*

    :returns: List of once controlled transform nodes, that are no 
              longer controlled.
    :rtype: [str, ..]
    """
    if current_frame is None:
        current_frame = maya.cmds.currentTime(query=True)
    assert current_frame is not None

    # Find controlled nodes from controller nodes
    ctrl_to_ctrlled_map = {}
    for src_node in nodes:
        constraints = _get_constraints_from_ctrls(src_node)
        dests = _get_destination_nodes_from_ctrls(constraints)
        if len(dests) == 0:
            continue
        ctrl_to_ctrlled_map[src_node] = (constraints, dests)

    # Query keyframe times on each node attribute
    key_times_map = time_utils.get_keyframe_times_for_node_attrs(nodes, TFM_ATTRS)

    # Query transform matrix on controlled nodes.
    cache = tfm_utils.TransformMatrixCache()
    for src_node, (constraints, dst_nodes) in ctrl_to_ctrlled_map.items():
        times = key_times_map.get(src_node, [current_frame])
        assert len(times) > 0
        ctrl = tfm_utils.TransformNode(node=src_node)
        cache.add_node(ctrl, times)
        for dst_node in dst_nodes:
            dst = tfm_utils.TransformNode(node=dst_node)
            cache.add_node(dst, times)
    cache.process(eval_mode=eval_mode)

    # Get Controlled nodes
    ctrlled_nodes = set()
    for src_node, (_, dst_nodes) in ctrl_to_ctrlled_map.items():
        for dst_node in dst_nodes:
            ctrlled_nodes.add(dst_node)

    # Delete constraints on controlled nodes.
    const_nodes = set()
    for src_node, (constraints, _) in ctrl_to_ctrlled_map.items():
        const_nodes |= constraints
    if len(const_nodes) > 0:
        maya.cmds.delete(list(const_nodes))

    # Set keyframes (per-frame) on controlled nodes
    anim_curves = []
    for src_node, (_, dst_nodes) in ctrl_to_ctrlled_map.items():
        src_times = key_times_map.get(src_node, [current_frame])
        assert len(src_times) > 0
        ctrl = tfm_utils.TransformNode(node=src_node)
        for dst_node in dst_nodes:
            dst = tfm_utils.TransformNode(node=dst_node)
            tfm_utils.set_transform_values(cache, src_times, ctrl, dst,
                                           delete_static_anim_curves=False)

            # Re-parent controller child nodes under controlled node.
            ctrl_children = maya.cmds.listRelatives(
                src_node,
                children=True,
                shapes=False,
                fullPath=True,
                type='transform',
            ) or []
            for child_node in ctrl_children:
                maya.cmds.parent(child_node, dst_node, absolute=True)

            src_had_keys = key_times_map.get(src_node) is not None
            if src_had_keys is True:
                continue
            # Maintain that destination node will not have keyframes now, the
            # same as the source node.
            dst_node = dst.get_node()
            keyable_attrs = _get_keyable_attrs(dst_node, TFM_ATTRS)
            anim_curves += anim_utils.get_anim_curves_from_nodes(
                list(keyable_attrs),
            )
    anim_curves = [n for n in anim_curves
                   if node_utils.node_is_referenced(n) is False]
    if len(anim_curves) > 0:
        maya.cmds.delete(anim_curves)

    # Delete controller nodes
    ctrl_nodes = ctrl_to_ctrlled_map.keys()
    if len(ctrl_nodes) > 0:
        maya.cmds.delete(ctrl_nodes)
    return list(ctrlled_nodes)
