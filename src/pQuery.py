#!/usr/bin/env python
#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

# A poor man's attempt at a jQuery clone done in Python for Ignifuga

from ignifuga.Entity import Entity
from ignifuga.Scene import Scene
from ignifuga.components.Component import Component
from ignifuga.components.Action import Action
from ignifuga.Gilbert import Gilbert
import re, inspect
#if ROCKET
import _rocketcore as rocket
#endif

class pQueryResult(list):
    """ A pQuery results holder, returned when you request an attribute from a pQuery wrapper
    It's essentially a list of tuples containing (target, property_name) with a few convenience operations
    """
    def __iter__(self):
        for target,name in super(pQueryResult, self).__iter__():
            try:
                value = getattr(target, name)
            except:
                value = None
            yield value

    def __getitem__(self, key):
        try:
            key = int(key)
        except:
            raise TypeError('pQueryResult only accepts integers as keys')
        if key < len(self):
            target,name = super(pQueryResult, self).__getitem__(key)
            return getattr(target,name)

        return None

    def __add__(self, value):
        ret = []
        if hasattr(value, '__iter__'):
            # Add a list of values in order to each of the targets
            ndx = 0
            target_len = len(self)
            for v in value:
                if ndx < target_len:
                    target, name = self[ndx]
                    ret.append(getattr(target, name) + v)
                else:
                    break
                ndx+=1
            return ret

        # A scalar value
        for target,name in super(pQueryResult, self).__iter__():
            ret.append(getattr(target, name) + value)

        return ret

    def __radd__(self, value):
        return self.__add__(value)

    def __sub__(self, value):
        ret = []
        if hasattr(value, '__iter__'):
            # Add a list of values in order to each of the targets
            ndx = 0
            target_len = len(self)
            for v in value:
                if ndx < target_len:
                    target, name = self[ndx]
                    ret.append(getattr(target, name) - v)
                else:
                    break
                ndx+=1
            return ret

        # A scalar value
        for target,name in super(pQueryResult, self).__iter__():
            ret.append(getattr(target, name) - value)

        return ret

    def __rsub__(self, value):
        ret = []
        if hasattr(value, '__iter__'):
            # Add a list of values in order to each of the targets
            ndx = 0
            target_len = len(self)
            for v in value:
                if ndx < target_len:
                    target, name = self[ndx]
                    ret.append(v - getattr(target, name))
                else:
                    break
                ndx+=1
            return ret

        # A scalar value
        for target,name in super(pQueryResult, self).__iter__():
            ret.append(value - getattr(target, name))

        return ret

    def __mul__(self, value):
        ret = []
        if hasattr(value, '__iter__'):
            # Add a list of values in order to each of the targets
            ndx = 0
            target_len = len(self)
            for v in value:
                if ndx < target_len:
                    target, name = self[ndx]
                    ret.append(getattr(target, name) * v)
                else:
                    break
                ndx+=1
            return ret

        # A scalar value
        for target,name in super(pQueryResult, self).__iter__():
            ret.append(getattr(target, name) * value)

        return ret

    def __rmul__(self, value):
        return self.__mul__(value)

    def __div__(self, value):
        ret = []
        if hasattr(value, '__iter__'):
            # Add a list of values in order to each of the targets
            ndx = 0
            target_len = len(self)
            for v in value:
                if ndx < target_len:
                    target, name = self[ndx]
                    ret.append(getattr(target, name) / v)
                else:
                    break
                ndx+=1
            return ret

        # A scalar value
        for target,name in super(pQueryResult, self).__iter__():
            ret.append(getattr(target, name) / value)

        return ret

    def __rdiv__(self, value):
        ret = []
        if hasattr(value, '__iter__'):
            # Add a list of values in order to each of the targets
            ndx = 0
            target_len = len(self)
            for v in value:
                if ndx < target_len:
                    target, name = self[ndx]
                    ret.append(v/getattr(target, name))
                else:
                    break
                ndx+=1
            return ret

        # A scalar value
        for target,name in super(pQueryResult, self).__iter__():
            ret.append(value / getattr(target, name))

        return ret

    def __iadd__(self, value):
        if hasattr(value, '__iter__'):
            # Add a list of values in order to each of the targets
            ndx = 0
            target_len = len(self)
            for v in value:
                if ndx < target_len:
                    target, name = self[ndx]
                    setattr(target, name, getattr(target,name) + v)
                else:
                    break
                ndx+=1
            return self

        # A scalar value
        for target,name in super(pQueryResult, self).__iter__():
            setattr(target, name, getattr(target, name) + value)

        return self

    def __isub__(self, value):
        if hasattr(value, '__iter__'):
            # Add a list of values in order to each of the targets
            ndx = 0
            target_len = len(self)
            for v in value:
                if ndx < target_len:
                    target, name = self[ndx]
                    setattr(target, name, getattr(target,name)-v)
                else:
                    break
                ndx+=1
            return self

        # A scalar value
        for target,name in super(pQueryResult, self).__iter__():
            setattr(target, name, getattr(target, name) - value)

        return self

    def __imul__(self, value):
        if hasattr(value, '__iter__'):
            # Add a list of values in order to each of the targets
            ndx = 0
            target_len = len(self)
            for v in value:
                if ndx < target_len:
                    target, name = self[ndx]
                    setattr(target, name, getattr(target,name)*v)
                else:
                    break
                ndx+=1
            return self

        # A scalar value
        for target,name in super(pQueryResult, self).__iter__():
            setattr(target, name, getattr(target, name) * value)

        return self

    def __idiv__(self, value):
        if hasattr(value, '__iter__'):
            # Add a list of values in order to each of the targets
            ndx = 0
            target_len = len(self)
            for v in value:
                if ndx < target_len:
                    target, name = self[ndx]
                    setattr(target, name, getattr(target,name)/v)
                else:
                    break
                ndx+=1
            return self

        # A scalar value
        for target,name in super(pQueryResult, self).__iter__():
            setattr(target, name, getattr(target, name) / value)

        return self

    def __call__(self, *args, **kwargs):
        ret = []
        for target,name in super(pQueryResult, self).__iter__():
            try:
                f = getattr(target, name)
                ret.append(f(*args, **kwargs))
            except:
                pass

        return ret



class pQueryWrapper(object):
    TYPE_UNKNOWN = 0
    TYPE_IGNIFUGA = 1
    TYPE_ROCKET = 2

    def __init__(self, targets, type):
        # Do assignment like this to avoid endless loops due to __getattr__
        self.__dict__['_targets'] = targets
        self.__dict__['_type'] = type

    @property
    def type(self):
        return self._type

    @property
    def targets(self):
        return self._targets

    def pQuery(self, selector, context = None):
        return pQuery(selector, pQuery(context, self))

    def __repr__(self):
        if self.type == pQueryWrapper.TYPE_IGNIFUGA:
            type = 'Ignifuga'
        elif self.type == pQueryWrapper.TYPE_ROCKET:
            type = 'Rocket'
        else:
            type = 'unknown'
        return "pQuery Wrapper of type %s with %d targets: %s" % (type, len(self._targets), self._targets)

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]

        ret = pQueryResult()
        for target in self._targets:
            ret.append((target,name))

        return ret

    def __setattr__( self, name, value):
        if hasattr(value, '__iter__'):
            # Assign a list of values in order to each of the targets
            ndx = 0
            targets = self._targets
            target_len = len(targets)
            for v in value:
                if ndx < target_len:
                    setattr(targets[ndx], name, v)
                else:
                    break
                ndx+=1
            return

        # Assign a scalar value (int, float, string, etc) to every target
        for target in self._targets:
            try:
                setattr(target,name, value)
            except:
                pass

    def __getitem__(self, key):
        try:
            key = int(key)
        except:
            raise TypeError('pQueryWrapper only accepts integers as keys')
        if key < len(self._targets):
            return self._targets[key]

        return None

class pQueryWrapperRocket(pQueryWrapper):
    """ Adds some jQuery inspired methods to the standard wrapper for use with Rocket elements
    Most of this stuff returns a single value, but when used for setting it sets the value for all targeted items
    """

    # CSS stuff: http://api.jquery.com/category/css/

    def addClass(self, name):
        """Adds the specified class(es) to each of the set of matched elements."""
        for target in self._targets:
            for classname in name.split(' '):
                if not target.IsClassSet(classname):
                    target.SetClass(classname, True)

    def css(self, name, value=None):
        """ Get/set the value of a style property for the first element in the set of matched elements."""
        if self._targets:
            if value is None:
                return self._targets[0].GetProperty(name)
            else:
                for target in self._targets:
                    target.SetProperty(name, value)

        return None

    def hasClass(self, name):
        """Determine whether any of the matched elements are assigned the given class."""
        for target in self._targets:
            if target.IsClassSet(name):
                return True

        return False

    def height(self, value=None):
        """Get/set the current computed height for the first element in the set of matched elements."""
        if self._targets:
            if value is None:
                return self._targets[0].offset_height
            else:
                for target in self._targets:
                    target.SetProperty('height', value)

        return None

    def innerHeight(self):
        """Get the current computed height for the first element in the set of matched elements, including padding but not border."""
        if self._targets:
            return self._targets[0].client_height
        return None

    def innerWidth(self):
        """Get the current computed width for the first element in the set of matched elements, including padding but not border."""
        if self._targets:
            return self._targets[0].client_width
        return None

    def offset(self, value=None):
        """Get/set the current coordinates of the first element in the set of matched elements, relative to the document."""
        if self._targets:
            if value is None:
                return self._targets[0].absolute_left, self._targets[0].absolute_top
            else:
                for target in self._targets:
                    try:
                        target.SetProperty('left', value[0])
                        target.SetProperty('top', value[1])
                    except:
                        pass

        return None

    def position(self):
        """Get the current coordinates of the first element in the set of matched elements, relative to the offset parent."""
        if self._targets:
            return self._targets[0].offset_left, self._targets[0].offset_top

        return None

    def removeClass(self, name):
        """Remove a single class from each element in the set of matched elements."""
        for target in self._targets:
            for classname in name.split(' '):
                if target.IsClassSet(classname):
                    target.SetClass(classname, False)

    def scrollLeft(self, value=None):
        """Get/set the current horizontal position of the scroll bar for the first element in the set of matched elements."""
        if self._targets:
            if value is None:
                return self._targets[0].scroll_left
            else:
                for target in self._targets:
                    target.scroll_left = value

        return None

    def scrollTop(self, value=None):
        """Get/set the current vertical position of the scroll bar for the first element in the set of matched elements."""
        if self._targets:
            if value is None:
                return self._targets[0].scroll_top
            else:
                for target in self._targets:
                    target.scroll_top = value

        return None

    def toggleClass(self, name):
        """Remove a single class, multiple classes, or all classes from each element in the set of matched elements."""
        for target in self._targets:
            for classname in name.split(' '):
                if not target.IsClassSet(classname):
                    target.SetClass(classname, True)
                else:
                    target.SetClass(classname, False)

    def width(self, value=None):
        """Get/set the current computed width for the first element in the set of matched elements."""
        if self._targets:
            if value is None:
                return self._targets[0].offset_width
            else:
                for target in self._targets:
                    target.SetProperty('width', value)

        return None

    def animate(self, properties, duration = 0.400, easing='linear',complete = None):
        pass


    # Attributes: http://api.jquery.com/category/attributes/

    def attr(self, name, value=None):
        """Get/set the value of an attribute for the first element in the set of matched elements."""
        if self._targets:
            if value is None:
                return self._targets[0].GetAttribute(name)
            else:
                for target in self._targets:
                    target.SetAttribute(name, value)

        return None

    def html(self, value=None):
        """Get/set the value of an attribute for the first element in the set of matched elements."""
        if self._targets:
            if value is None:
                return self._targets[0].inner_rml
            else:
                for target in self._targets:
                    target.inner_rml = value

        return None

    def rml(self, value=None):
        return self.html(value)

    def val(self, value=None):
        if self._targets:
            try:
                if value is None:
                    return self._targets[0].text
                else:
                    for target in self._targets:
                        target.text = value
            except:
                pass

        return None

    # Events: http://api.jquery.com/category/events/
    def bind(self, eventType, handler, capture_phase=False):
        """Attach a handler to an event for the elements."""
        for target in self._targets:
            target.AddEventListener(eventType, handler, capture_phase)

    def unbind(self, eventType, handler=None, capture_phase=False):
        """Attach a handler to an event for the elements."""
        for target in self._targets:
            if handler is not None:
                target.RemoveEventListener(eventType, handler, capture_phase)
            else:
                target.RemoveEventListener(eventType)


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
            if part != '':
                selector_parts.append(part)
                selector = selector[len(part):]
            else:
                break

    return selector_parts

def _pQueryIgnifuga(selector, targets):
    """ Filter targets according to the selector provided. See pQuery for a resume of selector options
        No "or" operations are supported here, that's handled by the pQuery function
    """

    if selector == '':
        return targets

    # Make a copy of the incoming targets
    targets = targets[:]
    _targets = []

    if inspect.isclass(selector):
        # Selector is a python class
        for target in targets:
            if isinstance(target, Scene):
                for entity in target.entities.itervalues():
                    if isinstance(entity, selector):
                        _targets.append(entity)
                    for component in entity.components.itervalues():
                        if isinstance(component, selector):
                            _targets.append(component)
            elif isinstance(target, Entity):
                for component in target.components.itervalues():
                    if isinstance(component, selector):
                        _targets.append(component)

        return _targets

    # String selector
    r_parenthesis = re.compile('\(([^\)]*)\)')

    selector_parts = _splitSelector(selector)

    for selector in selector_parts:
        selector = selector.strip()

        # Apply selectors
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
                for target in targets:
                    if isinstance(target, Scene):
                        # Select all entities and components in the scene
                        for entity in target.entities.itervalues():
                            _targets.append(entity)
                            for component in entity.components.itervalues():
                                _targets.append(component)
                    elif isinstance(target, Entity):
                        # Select all components in the entity
                        for component in target.components.itervalues():
                            _targets.append(component)
            elif selector.startswith('#'):
                # selector targets by id
                id = selector[1:]
                for target in targets:
                    if isinstance(target, Scene):
                        # selector the scene and find entities and components matching the id
                        for entity in target.entities.itervalues():
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
                        for entity in target.entities.itervalues():
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
                        for component in target.components.itervalues():
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
                                    _targets.append(target.entities.values()[value])
                            elif isinstance(target, Entity):
                                if len(target.components) > value:
                                    _targets.append(target.components.values()[value])
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
                # Last chance, test if it is a class selector (a string that says "Entity" for example)
                for target in targets:
                    if isinstance(target, Scene):
                        for entity in target.entities.itervalues():
                            if selector in Entity.__inheritors__:
                                _class = Entity.__inheritors__[selector]
                                if isinstance(entity, _class):
                                    _targets.append(entity)
                            elif selector in Component.__inheritors__:
                                _class = Component.__inheritors__[selector]
                                for component in entity.components.itervalues():
                                    if isinstance(component, _class):
                                        _targets.append(component)
                    elif isinstance(target, Entity):
                        if selector in Component.__inheritors__:
                            _class = Component.__inheritors__[selector]
                            for component in target.components.itervalues():
                                if isinstance(component, _class):
                                    _targets.append(component)

            targets = _targets[:]

    return targets





#if ROCKET
def _pQueryRocket(selector, targets):
    """ Filter targets according to the selector provided. See pQuery for a resume of selector options
        No "or" operations are supported here, that's handled by the pQuery function
    """

    if selector == '':
        return targets

    # Make a copy of the incoming targets
    targets = targets[:]
    _targets = []

    # String selector
    r_parenthesis = re.compile('\(([^\)]*)\)')

    selector_parts = _splitSelector(selector)

    for selector in selector_parts:
        selector = selector.strip()

        # Apply selectors
        if len(targets) > 0:
            if selector == '':
                # No selector
                _targets = targets
            elif selector == '*':
                # Select every children down to the last level
                while targets:
                    target = targets.pop()
                    for child in target.child_nodes:
                        targets.append(child)
                        if child not in _targets:
                            _targets.append(child)

            elif selector.startswith('#'):
                # selector targets by id
                id = selector[1:]
                for target in targets:
                    element = target.GetElementById(id)
                    if element is not None:
                        _targets.append(element)
            elif selector.startswith('.'):
                # selector targets by class
                classname = selector[1:]
                for target in targets:
                    elements = target.GetElementsByClassName(classname)
                    for element in elements:
                        if element not in _targets:
                            _targets.append(element)
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
                        for component in target.components.itervalues():
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
                                    _targets.append(target.entities.values()[value])
                            elif isinstance(target, Entity):
                                if len(target.components) > value:
                                    _targets.append(target.components.values()[value])
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
                # Last chance, test if it is a tag selector (ie body, document, etc)
                for target in targets:
                    elements = target.GetElementsByTagName(selector)
                    for element in elements:
                        if element not in _targets:
                            _targets.append(element)

            targets = _targets[:]

    return targets

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
        return pQueryWrapper([selector,], pQueryWrapper.TYPE_IGNIFUGA)
    #if ROCKET
    elif isinstance(selector, rocket.Document) or isinstance(selector, rocket.Element):
        return pQueryWrapperRocket([selector,], pQueryWrapper.TYPE_ROCKET)
    #endif
    elif inspect.isclass(selector):
        pass
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
        type = pQueryWrapper.TYPE_IGNIFUGA
        context = pQuery(Gilbert().scene)

    if inspect.isclass(selector):
        return pQueryWrapper(_pQueryIgnifuga(selector, context.targets), pQueryWrapper.TYPE_IGNIFUGA)

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
    if type == pQueryWrapper.TYPE_IGNIFUGA:
        for selector in selectors:
            for target in _pQueryIgnifuga(selector, context.targets):
                if target not in targets:
                    targets.append(target)
        return pQueryWrapper(targets, type)

    #if ROCKET
    elif type == pQueryWrapper.TYPE_ROCKET:
            for selector in selectors:
                for target in _pQueryRocket(selector, context.targets):
                    if target not in targets:
                        targets.append(target)
            return pQueryWrapperRocket(targets, type)
    #endif



