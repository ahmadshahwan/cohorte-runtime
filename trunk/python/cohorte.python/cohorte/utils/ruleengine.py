#!/usr/bin/env python
# -- Content-Encoding: UTF-8 --
"""
COHORTE Utilities: Rule engine, based on Intellect

**WARNING:**
This module uses the ``Intellect`` module.

:author: Thomas Calmant
:license: GPLv3
"""

# Documentation strings format
__docformat__ = "restructuredtext en"

# Boot module version
__version__ = "1.0.0"

# ------------------------------------------------------------------------------

# Intellect (rule engine)
import intellect.Intellect.Intellect as Intellect
import intellect.Intellect.Callable as Callable

# Standard library
import keyword
import re

# ------------------------------------------------------------------------------

class RuleEngine(Intellect):
    """
    Extension of the Intellect rule engine
    """
    def __init__(self):
        """
        Sets up the Intellect
        """
        # Parent constructor
        Intellect.__init__(self)

        # Dispatched methods (Name -> Method)
        self._dispatch = {}


    def __check_name(self, name):
        """
        Checks if the given name is a valid Python identifier
        
        :param name: A string
        :return: True if the string can be a valid Python identifier
        """
        if name in keyword.kwlist:
            # Keyword name -> bad
            return False

        # Match the name token
        return re.match(r'^[a-z_][a-z0-9_]*$', name, re.I) is not None


    def add_callable(self, method, name=None):
        """
        Allows a method to be used from rules
        
        :param method: A reference to the method
        :param name: The method name
        :return: The name of the method (given or computed)
        :raise KeyError: The method name is already used
        :raise ValueError: Invalid name or method
        """
        if method is None or not hasattr(method, '__call__'):
            raise ValueError("Invalid method reference")

        if not name:
            # Compute the name of method
            name = method.__name__

        elif not self.__check_name(name):
            # The name can't be a Python identifier
            raise ValueError("Invalid method name: {0}".format(name))

        # Check name usage
        if name in self._dispatch:
            raise KeyError("Already known method name: {0}".format(name))

        # Add the method to the dispatch dictionary
        self._dispatch[name] = Callable(method)
        return name


    def remove_callable(self, name):
        """
        Removes the method with the given name
        
        :param name: A method name (result of add_callable())
        :raise KeyError: Unknown method name
        """
        del self._dispatch[name]


    def clear(self):
        """
        Clears rule engine knowledge, policies and the dispatch dictionary
        """
        self._dispatch.clear()
        self.forget_all()


    def __getattr__(self, item):
        """
        Uses the dispatch dictionary to find a method used by the rules
        
        :param item: Item to search for
        :return: The found item
        :raise AttributeError: Item not found
        """
        try:
            # Get the item
            return self._dispatch[item]

        except KeyError:
            # Item not found
            raise AttributeError("Unknown attribute: {0}".format(item))