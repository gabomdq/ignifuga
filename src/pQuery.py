#!/usr/bin/env python
#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# A poor man's attempt at a jQuery clone done in Python for Ignifuga

from ignifuga.Entity import Entity
from ignifuga.Scene import Scene
from ignifuga.components.Component import Component
from ignifuga.Gilbert import Gilbert
import re
#if ROCKET
import _rocketcore as rocket
#endif

class pQueryWrapper(object):
    TYPE_UNKNOWN = 0
    TYPE_IGNIFUGA_OBJ = 1
    TYPE_IGNIFUGA_STR = 2
    TYPE_ROCKET_OBJ = 3
    TYPE_ROCKET_STR = 4

    def __init__(self, targets, type):
        self._targets = targets
        self._type = type

    @property
    def type(self):
        return self._type

    @property
    def targets(self):
        return self._targets

    def pQuery(self, selector, context = None):
        return pQuery(selector, pQuery(context, self))


def _splitSelector(selector):

    # Process the selectors
    selector_parts = []
    r_nonalphanum = re.compile('[^A-z0-9]')
    r_bracket = re.compile('\[[^\]]*\]')
    while selector != '':
        if selector[0] == ':':
            selector = selector[1:]
            # Split the selector on the next non alphanumeric character
            rr = r_nonalphanum.search(selector)
            if rr is not None:
                part = selector[rr.span()[0]]
                selector_parts.append(':'+part)
                selector = selector[len(part):]
            else:
                selector_parts.append(':'+selector)
                selector = ''
        elif selector[0] == '[':
            # Pick up everything from [ to the next ]
            rr = r_bracket.match(selector)
            if rr is not None:
                part = rr.group(0)
            else:
                part = selector
            selector_parts.append(part)
            selector = selector[len(part):]
        else:
            # Split the selector on the next space
            part = selector.split(' ')[0]
            selector_parts.append(part)
            selector = selector[len(part):]

    return selector_parts

def _pQueryIgnifuga(selector, targets):
    """ Filter targets according to the selector provided. See pQuery for a resume of selector options
        No "or" operations are supported here, that's handled by the pQuery function
    """

    if selector == '':
        return targets

    # Make a copy of the incoming targets
    targets = targets[:]

    r_parenthesis = re.compile('\(([^\)]*)\)')

    _targets = []

    selector_parts = _splitSelector(selector)

    for selector in selector_parts:
        selector = selector.strip()

        # Apply selectoring
        if len(targets) > 0:
            if selector == '':
                # No selector
                _targets = targets

            elif selector.startswith('~'):
                # Special case, the scene selector (~) ignores everything that came before it
                if selector == '~':
                    _targets = [Gilbert().scene,]
                else:
                    selector = selector[1:]
                    if selector in Gilbert().scenes:
                        _targets = [Gilbert().scenes[selector]]
                    else:
                        _targets = []
            elif selector == '*':
                # Select everything
                if isinstance(target, Scene):
                    # Select all entities and components in the scene
                    for entity in target.entities:
                        _targets.append(entity)
                        for component in entity.components:
                            _targets.append(component)
                elif isinstance(target, Entity):
                    # Select all components in the entity
                    for component in target.components:
                        _targets.append(component)
            elif selector.startswith('#'):
                # selector targets by id
                id = selector[1:]
                for target in targets:
                    if isinstance(target, Scene):
                        # selector the scene and find entities and components matching the id
                        for entity in target.entities:
                            if entity.id == id:
                                _targets.append(entity)
                            component = target.getComponent(id)
                            if component is not None:
                                _targets.append(component)
                    elif isinstance(target, Entity):
                        # selector the entity and find a component matching the id
                        component = target.getComponent(id)
                        if component is not None:
                            _targets.append(component)
            elif selector.startswith('.'):
                # selector targets by tag
                tag = selector[1:]
                for target in targets:
                    if isinstance(target, Scene):
                        # selector the scene and find entities and components matching the tag
                        for entity in target.entities:
                            if tag in entity.tags:
                                _targets.append(entity)
                            for component in entity.getComponentsByTag(tag):
                                _targets.append(component)
                    elif isinstance(target, Entity):
                        # selector the entity and find components matching the tag
                        for component in target.getComponentsByTag(tag):
                            _targets.append(component)
            elif selector.startswith('['):
                # selector by attribute
                selector = selector[1:-1] # remove [ and ]

                op = None
                if '|=' in selector:
                    # Attribute Contains Prefix Selector [name|="value"] - Selects elements that have the specified attribute with a value either equal to a given string or starting with that string followed by a hyphen (-).
                    name, value = selector.split('|=')
                    op = '|'
                elif '*=' in selector:
                    # Attribute Contains Selector [name*="value"] - Selects elements that have the specified attribute with a value containing the a given substring.
                    name, value = selector.split('*=')
                    op = '*'
                elif '~=' in selector:
                    # Attribute Contains Word Selector [name~="value"] - Selects elements that have the specified attribute with a value containing a given word, delimited by spaces.
                    name, value = selector.split('~=')
                    op = '~'
                elif '$=' in selector:
                    # Attribute Ends With Selector [name$="value"] - Selects elements that have the specified attribute with a value ending exactly with a given string. The comparison is case sensitive.
                    name, value = selector.split('$=')
                    op = '$'
                elif '!=' in selector:
                    # Attribute Not Equal Selector [name!="value"] - Select elements that either don't have the specified attribute, or do have the specified attribute but not with a certain value.
                    name, value = selector.split('!=')
                    op = '!'
                elif '^=' in selector:
                    # Attribute Starts With Selector [name^="value"] - Selects elements that have the specified attribute with a value beginning exactly with a given string.
                    name, value = selector.split('^=')
                    op = '^'
                elif '=' in selector:
                    # Attribute Equals Selector [name="value"] - Selects elements that have the specified attribute with a value exactly equal to a certain value.
                    name, value = selector.split('=')
                    op = '='

                if op != None:
                    for target in targets:
                        if hasattr(target, name):
                            tvalue = str(getattr(target, name))
                            if op == '|':
                                if tvalue == value or tvalue.startswith(value+'-'):
                                    _targets.append(target)
                            elif op == '*':
                                if value in tvalue:
                                    _targets.append(target)
                            elif op == '~':
                                if " %s " % value in tvalue:
                                    _targets.append(target)
                            elif op == '$':
                                if tvalue.endswith(value):
                                    _targets.append(target)
                            elif op == '!':
                                if tvalue != value:
                                    _targets.append(target)
                            elif op == '^':
                                if tvalue.startswith(value):
                                    _targets.append(target)
                            elif op == '=':
                                if tvalue == value:
                                    _targets.append(target)

            elif selector == ':active' or selector==':enabled':
                # selector by the active attribute
                for target in targets:
                    if isinstance(target, Scene):
                        # Scene is active if it's the current scene
                        if Gilbert().scene == target:
                            _targets.append(target)
                    elif isinstance(target, Entity):
                        # Entity is active if it belongs to the active scene
                        if Gilbert().scene == target.scene():
                            _targets.append(target)
                    elif isinstance(target, Component):
                        # Component is active if it's marked as active
                        if target.active:
                            _targets.append(target)

            elif selector == ':inactive' or selector==':disabled':
                # selector by the active attribute
                for target in targets:
                    if isinstance(target, Scene):
                        # Scene is active if it's the current scene
                        if Gilbert().scene != target:
                            _targets.append(target)
                    elif isinstance(target, Entity):
                        # Entity is active if it belongs to the active scene
                        if Gilbert().scene != target.scene():
                            _targets.append(target)
                    elif isinstance(target, Component):
                        # Component is active if it's marked as active
                        if not target.active:
                            _targets.append(target)

            elif selector == ':even':
                for t in range(0, len(targets), 2):
                    _targets.append(targets[t])
            elif selector == ':odd':
                if len(targets) > 1:
                    for t in range(1, len(targets), 2):
                        _targets.append(targets[t])
            elif selector == ':empty':
                for target in targets:
                    if isinstance(target, Scene) and not target.entities:
                        # Empty scenes are scenes without entities
                        _targets.append(target)
                    elif isinstance(target, Entity) and not target.components:
                        # Empty entities are entities without components
                        if Gilbert().scene != target.scene():
                            _targets.append(target)
            elif selector == ':parent':
                # Select targets that have children (opposite of :empty)
                for target in targets:
                    if isinstance(target, Scene) and target.entities:
                        _targets.append(target)
                    elif isinstance(target, Entity) and target.components:
                        if Gilbert().scene != target.scene():
                            _targets.append(target)
            elif selector == ':first':
                _targets.append(targets[0])
            elif selector == ':last':
                _targets.append(targets[-1])
            elif selector == ':first-child':
                for target in targets:
                    if isinstance(target, Scene):
                        if target.entities:
                            _targets.append(target.entities.items()[0])
                    elif isinstance(target, Entity):
                        if target.components:
                            _targets.append(target.components.items()[0])
            elif selector == ':last-child':
                for target in targets:
                    if isinstance(target, Scene):
                        if target.entities:
                            _targets.append(target.entities.items()[-1])
                    elif isinstance(target, Entity):
                        if target.components:
                            _targets.append(target.components.items()[-1])
            elif selector == ':last-child':
                for target in targets:
                    if isinstance(target, Scene):
                        if len(target.entities) == 1:
                            _targets.append(target.entities.items()[0])
                    elif isinstance(target, Entity):
                        if len(target.components) == 1:
                            _targets.append(target.components.items()[0])
            elif selector == ':children' or selector == '>':
                for target in targets:
                    if isinstance(target, Scene):
                        for entity in target.entities:
                            _targets.append(entity)
                    elif isinstance(target, Entity):
                        for component in target.components:
                            _targets.append(component)
            elif selector == ':visible':
                # selector by the visibility attribute
                for target in targets:
                    if isinstance(target, Scene):
                        # Scene is visible if it's the current scene
                        if Gilbert().scene == target:
                            _targets.append(target)
                    elif isinstance(target, Entity):
                        # Entity is visible if it has a visible property and belongs to the current scene
                        try:
                            if Gilbert().scene == target.scene() and target.visible:
                                _targets.append(target)
                        except:
                            pass
                    elif isinstance(target, Component):
                        # Component is visible if it has the visible attribute and is marked as such
                        try:
                            if target.visible:
                                _targets.append(target)
                        except:
                            pass
            elif selector == ':hidden':
                # selector by the visibility attribute (hidden)
                for target in targets:
                    if isinstance(target, Scene):
                        # Scene is visible if it's the current scene
                        if Gilbert().scene != target:
                            _targets.append(target)
                    elif isinstance(target, Entity):
                        # Entity is visible if it has a visible property and belongs to the current scene
                        try:
                            if Gilbert().scene != target.scene() or not target.visible:
                                _targets.append(target)
                        except:
                            pass
                    elif isinstance(target, Component):
                        # Component is visible if it has the visible attribute and is marked as such
                        try:
                            if not target.visible:
                                _targets.append(target)
                        except:
                            pass
            elif selector.startswith(':nth-child'):
                rr = r_parenthesis.search(selector)
                if rr is not None:
                    try:
                        value = int(rr.group(1))
                        for target in targets:
                            if isinstance(target, Scene):
                                if len(target.entities) > value:
                                    _targets.append(target.entities.items()[value])
                            elif isinstance(target, Entity):
                                if len(target.components) > value:
                                    _targets.append(target.components.items()[value])
                    except:
                        pass
            elif selector.startswith(':not'):
                rr = r_parenthesis.search(selector)
                if rr is not None:
                    value = rr.group(1)
                    __targets = _pQueryIgnifuga(value, targets[:])
                    for target in targets:
                        if target not in __targets:
                            _targets.append(target)

            else:
                # Finally, use selector as a python class specifier
                for target in targets:
                    if isinstance(target, Scene):
                         if selector in Entity.__inheritors__:
                            _class = Entity.__inheritors__[selector]
                            for entity in target.entities:
                                if isinstance(entity, _class):
                                    _targets.append(entity)
                    elif isinstance(target, Entity):
                        if selector in Component.__inheritors__:
                            _class = Component.__inheritors__[selector]
                            for component in target.components:
                                if isinstance(component, _class):
                                    _targets.append(component)

            targets = _targets[:]

    return targets





#if ROCKET
def _pQueryRocket(filter, targets):
    pass
#endif

def pQuery(selector, context = None):
    """
    selector and context are modeled after jQuery selectors. http://api.jquery.com/category/selectors/

    All Selector (“*”) - Selects all elements.
    :animated Selector - Select all elements that are in the progress of an animation at the time the selector is run.
    Attribute Contains Prefix Selector [name|="value"] - Selects elements that have the specified attribute with a value either equal to a given string or starting with that string followed by a hyphen (-).
    Attribute Contains Selector [name*="value"] - Selects elements that have the specified attribute with a value containing the a given substring.
    Attribute Contains Word Selector [name~="value"] - Selects elements that have the specified attribute with a value containing a given word, delimited by spaces.
    Attribute Ends With Selector [name$="value"] - Selects elements that have the specified attribute with a value ending exactly with a given string. The comparison is case sensitive.
    Attribute Equals Selector [name="value"] - Selects elements that have the specified attribute with a value exactly equal to a certain value.
    Attribute Not Equal Selector [name!="value"] - Select elements that either don't have the specified attribute, or do have the specified attribute but not with a certain value.
    Attribute Starts With Selector [name^="value"] - Selects elements that have the specified attribute with a value beginning exactly with a given string.
    :checked Selector - Matches all elements that are checked.
    Child Selector (“parent > child”) - Selects all direct child elements specified by "child" of elements specified by "parent".
    Class Selector (“.class”) - Selects all elements with the given class.
    :contains() Selector - Select all elements that contain the specified text.
    Descendant Selector (“ancestor descendant”) - Selects all elements that are descendants of a given ancestor.
    :disabled Selector - Selects all elements that are disabled.
    Element Selector (“element”) - Selects all elements with the given tag name.
    :empty Selector - Select all elements that have no children (including text nodes).
    :enabled Selector - Selects all elements that are enabled.
    :eq() Selector - Select the element at index n within the matched set.
    :even Selector - Selects even elements, zero-indexed. See also odd.
    :first-child Selector - Selects all elements that are the first child of their parent.
    :first Selector - Selects the first matched element.
    :focus selector - Selects element if it is currently focused.
    :gt() Selector - Select all elements at an index greater than index within the matched set.
    Has Attribute Selector [name] - Selects elements that have the specified attribute, with any value.
    :has() Selector - Selects elements which contain at least one element that matches the specified selector.
    :header Selector - Selects all elements that are headers, like h1, h2, h3 and so on.
    :hidden Selector - Selects all elements that are hidden.
    ID Selector (“#id”) - Selects a single element with the given id attribute.
    :last-child Selector
    Selects all elements that are the last child of their parent.
    :last Selector
    Selects the last matched element.
    :lt() Selector
    Select all elements at an index less than index within the matched set.
    Multiple Attribute Selector [name="value"][name2="value2"] - Matches elements that match all of the specified attribute filters.
    Multiple Selector (“selector1, selector2, selectorN”) - Selects the combined results of all the specified selectors.
    Next Adjacent Selector (“prev + next”) - Selects all next elements matching "next" that are immediately preceded by a sibling "prev".
    Next Siblings Selector (“prev ~ siblings”) - Selects all sibling elements that follow after the "prev" element, have the same parent, and match the filtering "siblings" selector.
    :not() Selector - Selects all elements that do not match the given selector.
    :nth-child() Selector - Selects all elements that are the nth-child of their parent.
    :odd Selector - Selects odd elements, zero-indexed. See also even.
    :only-child Selector - Selects all elements that are the only child of their parent.
    :parent Selector - Select all elements that are the parent of another element, including text nodes.
    :selected Selector - Selects all elements that are selected.
    :visible Selector - Selects all elements that are visible.

    selector and context can also be:

    a Rocket Element Python object
    a pQuery wrapper
    an Ignifuga Scene/Entity/Component
    "someclass" Selects an Ignifuga object class
    "#someid" Selects an Ignifuga Entity or component with a given id
    ".tag" Selects an Ignifuga Entity or component with a given tag
    ":entity" Select only entities
    ":component" Select only components
    ":active" (or :enabled) Select active entities/components
    ":inactive" (or :disabled) Select inactive entities/components
    ":children" (similar to jQuery's >) Select direct children of element
    "~" Selects the current Ignifuga Scene (ignores all other selectors)
    "~sceneid" Selects an Ignifuga Scene with a given id (ignores all other selectors)
    """

    # Figure out the type of query
    if isinstance(selector, pQueryWrapper):
        # A pQueryWrapper is not really a selector, return it as is
        return selector
    elif isinstance(selector,  Entity) or isinstance(selector, Component):
        return pQueryWrapper([selector,], pQueryWrapper.TYPE_IGNIFUGA_OBJ)
    #if ROCKET
    elif isinstance(selector, rocket.Document) or isinstance(selector, rocket.Element):
        return pQueryWrapper([selector,], pQueryWrapper.TYPE_ROCKET_OBJ)
    #endif
    elif isinstance(selector, basestring):
        # Cast out the unicode pariahs just in case
        selector = str(selector).strip()
    else:
        # Unknown selector, return an empty wrapper
        if context is None:
            return pQueryWrapper([], pQueryWrapper.TYPE_UNKNOWN)
        else:
            return pQueryWrapper(context.targets, context.type)


    # We arrive here only if we were provided a string selectors, so we need to figure out which type of query we got
    type = None
    if context is not None:
        context = pQuery(context)
        # Try to figure out the query type from the context
        if context.type != pQueryWrapper.TYPE_UNKNOWN:
            type = context.type

    if type is None:
        # No context given or the context does not have a known type, so we default to an Ignifuga query
        # with the current scene as context because we can't operate on Rocket without knowing the desired document
        type = pQueryWrapper.TYPE_IGNIFUGA_STR
        context = pQuery(Gilbert().scene)

    selector_parts = _splitSelector(selector)

    # Scan the selector for commas which act as the or operator
    new_selector = ''
    selectors = []
    for selector in selector_parts:
        if selector == ',':
            if new_selector != '':
                selectors.append(new_selector)
                new_selector = ''
        elif selector.startswith(','):
            new_selector += selector[1:]
            if new_selector != '':
                selectors.append(new_selector)
                new_selector = ''
        elif selector.endswith(','):
            new_selector += selector[:-1]
            if new_selector != '':
                selectors.append(new_selector)
                new_selector = ''
        else:
            new_selector += selector + ' '

    if new_selector != '':
        selectors.append(new_selector)

    targets = []
    if type == pQueryWrapper.TYPE_IGNIFUGA_STR:
        for selector in selectors:
            for target in _pQueryIgnifuga(selector, context.targets):
                if target not in targets:
                    targets.append(target)
    #if ROCKET
    elif type == pQueryWrapper.TYPE_ROCKET_STR:
            for selector in selectors:
                for target in _pQueryRocket(selector, context.targets):
                    if target not in targets:
                        targets.append(target)
    #endif

    return pQueryWrapper(targets, type)

