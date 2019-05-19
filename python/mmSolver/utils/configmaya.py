"""
Configuration module. GitHub issue #17.

There are many places to store and read data from in Maya.

- A Maya node
- The Maya scene file.
- The Python shared variables.
- The Maya preferences.

Each type of storage can be considered to have a different life-time.

The levels are (in ascending order):
- Maya Node
- Maya Scene
- Maya Session
- Maya Preferences

"""

import json

import maya.cmds
import mmSolver.logger

LOG = mmSolver.logger.get_logger()


def __get_data_on_node_attr(node_name, attr_name):
    """
    Get data from an node attribute.

    :param node_name: Node to get data from.
    :type node_name: str

    :param attr_name: The name of the attribute to get data from.
    :type attr_name: str

    :return: Arbitrary Plain-Old-Data data structures.
    :rtype: list of dict
    """
    ret = []
    attr_data = __get_value_on_node_attr(node_name, attr_name)
    if attr_data is None:
        return ret
    data = json.loads(attr_data)
    if isinstance(data, list):
        ret = data
    return ret


def __set_data_on_node_attr(node_name, attr_name, data):
    """
    Set arbitrary Plain-Old-Data onto a node.attr path.

    :param node_name: Node to store data on.
    :type node_name: str

    :param attr_name: Attribute name to store data with.
    :type attr_name: str

    :param data: The data to store.
    :type data: list or dict
    """
    assert isinstance(attr_name, (str, unicode))
    assert isinstance(data, (list, dict))
    node_attr = node_name + '.' + attr_name

    new_attr_data = json.dumps(data)
    old_attr_data = maya.cmds.getAttr(node_attr)
    if old_attr_data == new_attr_data:
        return  # no change is needed.

    maya.cmds.setAttr(node_attr, lock=False)
    maya.cmds.setAttr(node_attr, new_attr_data, type='string')
    maya.cmds.setAttr(node_attr, lock=True)
    return


def __get_value_on_node_attr(node_name, attr_name):
    """
    Get numeric value from an node attribute.

    :param node_name: Node to get value from.
    :type node_name: str

    :param attr_name: The name of the attribute to get value from.
    :type attr_name: str

    :return: A numeric value.
    :rtype: bool or float or int
    """
    attrs = maya.cmds.listAttr(node_name)
    if attr_name not in attrs:
        msg = 'attr_name not found on node: '
        msg += 'attr_name={name} node={node}'
        msg = msg.format(name=attr_name, node=node_name)
        raise ValueError(msg)
    node_attr = node_name + '.' + attr_name
    ret = maya.cmds.getAttr(node_attr)
    return ret


def __set_value_on_node_attr(node_name, attr_name, data):
    """
    Set value onto a node.attr path.

    :param node_name: Node to store value on.
    :type node_name: str

    :param attr_name: Attribute name to store value with.
    :type attr_name: str

    :param data: The numeric value to store.
    :type data: bool or float or int

    ;return: Nothing.
    :rtype: None
    """
    assert isinstance(attr_name, (str, unicode))
    assert isinstance(data, (bool, float, int))
    node_attr = node_name + '.' + attr_name
    maya.cmds.setAttr(node_attr, lock=False)
    maya.cmds.setAttr(node_attr, data)
    maya.cmds.setAttr(node_attr, lock=True)
    return


def get_node_option(node, name, default=None):
    # Get attribute value on the given node.
    pass


def set_node_option(node, name, value):
    # Set attribute value on the given node.
    pass


def get_scene_option(name, default=None):
    # Get a value from the scene.
    pass


def set_scene_option(name, value):
    # Set a value in the scene.
    pass


def get_session_option(name, default=None):
    # Get an option that lives in this Maya instance only.
    pass


def set_session_option(name, value):
    # Set an option that lives in this Maya instance only.
    pass


def get_preference_option(name, default=None):
    # Get a Maya preference from Maya (optionVar).
    pass


def set_preference_option(name, value):
    # Set a Maya preference to Maya (optionVar).
    pass


def save_preference_options():
    # Write all preferences to disk.
    pass