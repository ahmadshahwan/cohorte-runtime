#-- Content-Encoding: UTF-8 --
"""
Defines the iPOPO decorators classes to manipulate component factory classes

:author: Thomas Calmant
:copyright: Copyright 2012, isandlaTech
:license: GPLv3
:version: 0.2
:status: Alpha

..

    This file is part of iPOPO.

    iPOPO is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    
    iPOPO is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    
    You should have received a copy of the GNU General Public License
    along with iPOPO. If not, see <http://www.gnu.org/licenses/>.
"""

from psem2m import is_string
from psem2m.component import constants
from psem2m.component.ipopo import FactoryContext, Requirement

import inspect
import logging
import threading
import types

# ------------------------------------------------------------------------------

# Documentation strings format
__docformat__ = "restructuredtext en"

# Prepare the module logger
_logger = logging.getLogger("ipopo.decorators")

# ------------------------------------------------------------------------------

def _get_factory_context(cls):
    """
    Retrieves the factory context object associated to a factory. Creates it
    if needed
    
    :param cls: The factory class
    :return: The factory class context
    """
    context = getattr(cls, constants.IPOPO_FACTORY_CONTEXT_DATA, None)
    if context is None:
        context = FactoryContext()
        setattr(cls, constants.IPOPO_FACTORY_CONTEXT_DATA, context)

    return context


def _is_method_or_function(tested):
    """
    Tests if the given object is function or a method using the inspect
    module
    
    In Python 2.x classes, class functions are methods
    In Python 3.x classes, there are functions
    
    :param tested: An object to be tested
    :return: True if the tested object is a function or a method
    """
    return inspect.isfunction(tested) or inspect.ismethod(tested)


def _ipopo_setup_callback(cls, context):
    """
    Sets up the class _callback dictionary
    
    :param cls: The class to handle
    :param context: The factory class context
    """
    assert inspect.isclass(cls)
    assert isinstance(context, FactoryContext)

    if context.callbacks is not None:
        callbacks = context.callbacks.copy()

    else:
        callbacks = {}

    functions = inspect.getmembers(cls, _is_method_or_function)

    for name, function in functions:

        if not hasattr(function, constants.IPOPO_METHOD_CALLBACKS):
            # No attribute, get the next member
            continue

        method_callbacks = getattr(function, constants.IPOPO_METHOD_CALLBACKS)

        if not isinstance(method_callbacks, list):
            # Invalid content
            _logger.warning("Invalid attribute %s in %s", \
                            constants.IPOPO_METHOD_CALLBACKS, name)
            continue

        # Keeping it allows inheritance : by removing it, only the first
        # child will see the attribute -> Don't remove it

        # Store the callbacks
        for _callback in method_callbacks:
            if _callback in callbacks:
                _logger.warning("Redefining the _callback %s in '%s'. " \
                                "Previous _callback : '%s'.", \
                                _callback, name, \
                                callbacks[_callback].__name__)

            callbacks[_callback] = function

    # Update the factory context
    context.callbacks.clear()
    context.callbacks.update(callbacks)

# ------------------------------------------------------------------------------

def _append_object_entry(obj, list_name, entry):
    """
    Appends the given entry in the given object list.
    Creates the list field if needed.
    
    :param obj: The object that contains the list
    :param list_name: The name of the list member in *obj*
    :param entry: The entry to be added to the list
    """
    # Get the list
    try:
        obj_list = getattr(obj, list_name)
        if not obj_list:
            # Prepare a new dictionary dictionary
            obj_list = []

    except AttributeError:
        # We'll have to create it
        obj_list = []
        setattr(obj, list_name, obj_list)


    assert(isinstance(obj_list, list))

    # Set up the property, if needed
    if entry not in obj_list:
        obj_list.append(entry)

# ------------------------------------------------------------------------------

def _ipopo_class_field_property(name, value):
    """
    Sets up an iPOPO field property, using Python property() capabilities
    
    :param name: The property name
    :param value: The property default value
    :return: A generated Python property()
    """
    # The property lock
    lock = threading.RLock()

    def get_value(self):
        """
        Retrieves the property value, from the iPOPO dictionaries
        
        :return: The property value
        """
        getter = getattr(self, constants.IPOPO_PROPERTY_GETTER, None)
        if getter is not None:
            with lock:
                return getter(self, name)

        return value


    def set_value(self, new_value):
        """
        Sets the property value and trigger an update event
        
        :param new_value: The new property value
        :return: The new value
        """
        setter = getattr(self, constants.IPOPO_PROPERTY_SETTER, None)
        if setter is not None:
            with lock:
                return setter(self, name, new_value)

        return new_value

    return property(get_value, set_value)

# ------------------------------------------------------------------------------

class Instantiate:
    """
    Decorator that sets up a future instance of a component
    """
    def __init__(self, name, properties=None):
        """
        Sets up the decorator
        
        :param name: Instance name
        :param properties: Instance properties
        """
        if not isinstance(name, str):
            raise TypeError("Instance name must be a string")

        if properties is not None and not isinstance(properties, dict):
            raise TypeError("Instance properties must be a dictionary or None")

        if not name:
            raise ValueError("Invalid instance name '%s'", name)

        self.__name = name
        self.__properties = properties


    def __call__(self, factory_class):
        """
        Sets up and registers the instances descriptions
        
        :param factory_class: The decorated class
        """
        if not inspect.isclass(factory_class):
            raise TypeError("@ComponentFactory can decorate only classes, " \
                            "not '%s'" % type(factory_class).__name__)

        if hasattr(factory_class, constants.IPOPO_INSTANCES):
            instances = getattr(factory_class, constants.IPOPO_INSTANCES)

        else:
            instances = {}
            setattr(factory_class, constants.IPOPO_INSTANCES, instances)

        if self.__name in instances:
            _logger.warn("Component '%s' defined twice, new definition ignored",
                         self.__name)

        else:
            instances[self.__name] = self.__properties

        return factory_class

# ------------------------------------------------------------------------------

class ComponentFactory:
    """
    Decorator that sets up a component factory class
    """
    def __init__(self, name=None):
        """
        Sets up the decorator

        :param name: Name of the component factory
        """
        self.__factory_name = name


    def __call__(self, factory_class):
        """
        Sets up and registers the factory class

        :param factory_class: The decorated class
        """
        if not inspect.isclass(factory_class):
            raise TypeError("@ComponentFactory can decorate only classes, " \
                            "not '%s'" % type(factory_class).__name__)

        # Get the factory context
        context = _get_factory_context(factory_class)

        # Set the factory name
        if not self.__factory_name:
            self.__factory_name = factory_class.__name__ + "Factory"

        context.name = self.__factory_name

        # Find callbacks
        _ipopo_setup_callback(factory_class, context)

        # Add the factory context field (set it to None)
        setattr(factory_class, constants.IPOPO_FACTORY_CONTEXT, None)

        # Store a dictionary form of the factory context in the class
        # -> Avoids "class version" problems
        setattr(factory_class, constants.IPOPO_FACTORY_CONTEXT_DATA, \
                context.to_dictionary_form())

        return factory_class

# ------------------------------------------------------------------------------

class Property:
    """
    @Property decorator
    
    Defines a component property.
    """
    def __init__(self, field=None, name=None, value=None):
        """
        Sets up the property
        
        :param field: The property field in the class (can't be None nor empty)
        :param name: The property name (if None, this will be the field name)
        :param value: The property value
        :raise ValueError: If The name if None or empty
        """

        if not field:
            raise ValueError("@Property with name '%s' : field name missing" \
                             % name)

        if not name:
            # No name given : use the field name
            name = field

        self.__field = field
        self.__name = name
        self.__value = value


    def __call__(self, clazz):
        """
        Adds the property to the class iPOPO properties field.
        Creates the field if needed.
        
        :param clazz: The decorated class
        :raise TypeError: If *clazz* is not a type
        """
        if not inspect.isclass(clazz):
            raise TypeError("@Property can decorate only classes, not '%s'" \
                            % type(clazz).__name__)

        # Get the factory context
        context = _get_factory_context(clazz)

        # Set up the property in the class
        context.properties[self.__name] = self.__value

        # Associate the field to the property name
        context.properties_fields[self.__field] = self.__name

        # Inject a property in the class. The property will call an instance
        # level getter / setter, injected by iPOPO after the instance creation
        setattr(clazz, self.__field, \
                _ipopo_class_field_property(self.__name, self.__value))

        return clazz

# ------------------------------------------------------------------------------

class Provides:
    """
    @Provides decorator
    
    Defines an interface exported by a component.
    """
    def __init__(self, specifications=None):
        """
        Sets up the specifications
        
        :param specifications: A list of provided interface(s) name(s)
                               (can't be empty)
        :raise ValueError: If the name if None or empty
        """
        if not specifications:
            raise ValueError("Provided interface name can't be empty")

        if inspect.isclass(specifications):
            self.__specifications = [specifications.__name__]

        elif is_string(specifications):
            self.__specifications = [specifications]

        elif not isinstance(specifications, list):
            raise ValueError("Unhandled @Provides specifications type : %s" \
                             % type(specifications).__name__)

        else:
            self.__specification = specifications


    def __call__(self, clazz):
        """
        Adds the interface to the class iPOPO field.
        Creates the field if needed.
        
        :param clazz: The decorated class
        :raise TypeError: If *clazz* is not a type
        """

        if not inspect.isclass(clazz):
            raise TypeError("@Provides can decorate only classes, not '%s'" \
                            % type(clazz).__name__)

        # Get the factory context
        context = _get_factory_context(clazz)

        for spec in self.__specifications:
            if spec not in context.provides:
                # Avoid duplicates
                context.provides.append(spec)

        return clazz

# ------------------------------------------------------------------------------

class Requires:
    """
    @Requires decorator
    
    Defines a required component
    """
    def __init__(self, field="", specification="", aggregate=False, \
                 optional=False, spec_filter=None):
        """
        Sets up the requirement
        
        :param field: The injected field
        :param specification: The injected service specification
        :param aggregate: If true, injects a list
        :param optional: If true, this injection is optional
        :param spec_filter: An LDAP query to filter injected services upon their
                            properties
        :raise TypeError: A parameter has an invalid type
        :raise ValueError: An error occurred while parsing the filter
        """
        self.__field = field
        self.__requirement = Requirement(specification, aggregate, \
                                               optional, spec_filter)

    def __call__(self, clazz):
        """
        Adds the requirement to the class iPOPO field
        
        :param clazz: The decorated class
        :raise TypeError: If *clazz* is not a type
        """
        if not inspect.isclass(clazz):
            raise TypeError("@Provides can decorate only classes, not '%s'" \
                            % type(clazz).__name__)

        # Set up the property in the class
        context = _get_factory_context(clazz)
        context.requirements[self.__field] = self.__requirement

        return clazz

# ------------------------------------------------------------------------------

def Bind(method):
    """
    Bind callback decorator, called when a component is bound to a dependency.
    
    The decorated method must have the following prototype :
    
    .. python::
       def bind_method(self, injected_instance):
           '''
           Method called when a service is bound to the component
           
           :param injected_instance: The injected service instance.
           '''
           # ...
    
    If the service is a required one, the bind callback is called **before** the
    component is validated.
    
    Exceptions raised by an unbind callback are ignored.
    
    :param method: The decorated method
    :raise TypeError: The decorated element is not a function
    """
    if type(method) is not types.FunctionType:
        raise TypeError("@Bind can only be applied on functions")

    _append_object_entry(method, constants.IPOPO_METHOD_CALLBACKS, \
                         constants.IPOPO_CALLBACK_BIND)
    return method


def Unbind(method):
    """
    Unbind callback decorator, called when a component dependency is unbound.
    
    The decorated method must have the following prototype :
    
    .. python::
       def unbind_method(self, injected_instance):
           '''
           Method called when a service is bound to the component
           
           :param injected_instance: The injected service instance.
           '''
           # ...
    
    If the service is a required one, the unbind callback is called **after**
    the component has been invalidated.
    
    Exceptions raised by an unbind callback are ignored.
    
    :param method: The decorated method
    :raise TypeError: The decorated element is not a function
    """
    if type(method) is not types.FunctionType:
        raise TypeError("@Unbind can only be applied on functions")

    _append_object_entry(method, constants.IPOPO_METHOD_CALLBACKS, \
                         constants.IPOPO_CALLBACK_UNBIND)
    return method


def Validate(method):
    """
    Validation callback decorator, called when a component becomes valid,
    i.e. if all of its required dependencies has been injected.
    
    The decorated method must have the following prototype :
    
    .. python::
       def validation_method(self, bundle_context):
           '''
           Method called when the component is validated
           
           :param bundle_context: The component's bundle context
           '''
           # ...
    
    If the validation callback raises an exception, the component is considered
    not validated.
    
    If the component provides a service, the validation method is called before
    the provided service is registered to the framework.
    
    :param method: The decorated method
    :raise TypeError: The decorated element is not a function
    """
    if type(method) is not types.FunctionType:
        raise TypeError("@Validate can only be applied on functions")

    _append_object_entry(method, constants.IPOPO_METHOD_CALLBACKS, \
                         constants.IPOPO_CALLBACK_VALIDATE)
    return method


def Invalidate(method):
    """
    Invalidation callback decorator, called when a component becomes invalid,
    i.e. if one of its required dependencies disappeared
    
    The decorated method must have the following prototype :
    
    .. python::
       def invalidation_method(self, bundle_context):
           '''
           Method called when the component is invalidated
           
           :param bundle_context: The component's bundle context
           '''
           # ...
    
    Exceptions raised by an invalidation callback are ignored.
    
    If the component provides a service, the invalidation method is called after
    the provided service has been unregistered to the framework.
    
    :param method: The decorated method
    :raise TypeError: The decorated element is not a function
    """

    if type(method) is not types.FunctionType:
        raise TypeError("@Invalidate can only be applied on functions")

    _append_object_entry(method, constants.IPOPO_METHOD_CALLBACKS, \
                         constants.IPOPO_CALLBACK_INVALIDATE)
    return method
