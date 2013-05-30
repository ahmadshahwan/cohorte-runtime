#!/usr/bin/env python
# -- Content-Encoding: UTF-8 --
"""
COHORTE Composer Core: Composer beans

:author: Thomas Calmant
:license: GPLv3
"""

# Documentation strings format
__docformat__ = "restructuredtext en"

# Boot module version
__version__ = "1.0.0"

# ------------------------------------------------------------------------------

import pelix.ldapfilter as ldapfilter

# ------------------------------------------------------------------------------

class Composition(object):
    """
    Represents a whole composition, containing components and composites
    """
    def __init__(self, uid, name, source_file, timestamp):
        """
        Sets up members
        
        :param uid: UID of the composition, generated by the parser
        :param name: Name of composition (title, ...)
        :param source_file: Name of the root source file for this composition
        :param timestamp: Time of loading of this composition
        :raise ValueError: Invalid parameters
        """
        if not uid:
            raise ValueError("UID can't be empty")

        if not name:
            raise ValueError("Name can't be empty")

        # Read-only parameters
        self.__uid = uid
        self.__name = name
        self.__source = source_file
        self.__timestamp = timestamp

        # Set-once root composite
        self.__root = None


    @property
    def uid(self):
        """
        The UID of the composition
        """
        return self.__uid


    @property
    def name(self):
        """
        The name of the composition
        """
        return self.__name


    @property
    def source(self):
        """
        The name of the root file defining this composition
        """
        return self.__source


    @property
    def timestamp(self):
        """
        The date when this composition has been loaded
        """
        return self.__source


    @property
    def root(self):
        """
        The composition root composite
        """
        return self.__root


    @root.setter
    def root(self, root):
        """
        Sets the composition root composite
        """
        if not self.__root:
            self.__root = root


    def normalize(self):
        """
        Normalizes the root composite: links wires, ...
        Returning False doesn't mean that the composition is broken, but that
        there is a missing dependency inside the composition, and a parallel
        one might be instantiated to validate dependencies.
        
        :return: True if the normalization succeeded
        """
        return self.__root.normalize()


    def __repr__(self):
        """
        String representation of the composition
        """
        return "Composition({0}, {1}, {2}, {3})".format(self.__uid, self.__name,
                                                        self.__source,
                                                        self.__timestamp)

# ------------------------------------------------------------------------------

class Composite(object):
    """
    Represents a composite: a set of components
    """
    def __init__(self, uid, name, parent):
        """
        Sets up the composite
        
        :param uid: UID of the composite, generated by the parser
        :param name: Name of composite
        :param parent: The composite 
        :raise ValueError: Invalid parameters
        """
        if not uid:
            raise ValueError("UID can't be empty")

        if not name:
            raise ValueError("Name can't be empty")

        if '.' in name:
            raise ValueError("{0}: A composite name can't contain a '.' (dot)" \
                             .format(name))

        # Read-only parameters
        self.__uid = uid
        self.__name = name
        self.__parent = parent

        # Set-once parameter
        self.__fullname = None

        # Content of the composite: Name -> Bean
        self._components = {}
        self._composites = {}


    @property
    def uid(self):
        """
        The UID of the composite
        """
        return self.__uid


    @property
    def name(self):
        """
        The name of the composite
        """
        return self.__name


    def all_components(self):
        """
        Generator to recursively visit all components of this composition
        """
        for component in self._components.values():
            yield component

        for composite in self._composites.values():
            for component in composite.all_components():
                yield component


    @property
    def components(self):
        """
        The components right in this composite
        """
        return self._components.copy()


    @property
    def composites(self):
        """
        The composites right in this composite
        """
        return self._composites.copy()


    @property
    def parent(self):
        """
        The parent of this composite
        """
        return self.__parent


    @property
    def fullname(self):
        """
        The component full name
        """
        return self.__fullname


    @fullname.setter
    def fullname(self, name):
        """
        Sets the component full name if it is not yet set.
        """
        if not self.__fullname:
            self.__fullname = name


    def add_component(self, component):
        """
        Adds a component to this composite
        
        :param component: A component bean
        """
        # Compute the full name of the component
        name = component.name
        component.fullname = "{0}.{1}".format(self.__name, name)

        # Store the component
        self._components[name] = component


    def add_composite(self, composite):
        """
        Adds a composite to this one
        
        :param composite: A composite bean
        """
        # Compute the full name of the composite
        name = composite.name
        composite.fullname = "{0}.{1}".format(self.__name, name)

        # Store the component
        self._composites[name] = composite


    def find_component(self, name, caller=None, try_parent=True):
        """
        Recursively looks for a component endings with the given name, from
        leaves to the root component set.
        
        :param name: A component name (or the right part of its full name)
        :param caller: Child that called this method, to avoid looking twice
                       into it
        :param try_parent: If true, the composite must ask its parent to
                           continue the search.
        :return: The first matching component found, or None
        """
        if name in self._components:
            # Local name
            return self._components[name]

        # Try with full names
        for component in self._components.values():
            if component.fullname() == name:
                return component

        # Try with sub-components
        for composite in self._composites.values():
            # (Ignore calling child)
            if composite is not caller:
                result = composite.find_component(name, None, False)
                if result is not None:
                    # Found !
                    return result

        if try_parent and self.__parent is not None:
            # Ask to the parent to continue the search
            return self.__parent.find_component(name, self, True)


    def normalize(self):
        """
        Normalizes the root composite: links wires, ...
        """
        result = True

        # Link wires in the components
        for component in self._components.values():
            result &= component.link_wires(self)

        # Continue normalization
        for composite in self._composites.values():
            result &= composite.normalize()

        return result


    def __repr__(self):
        """
        String representation of the composite
        """
        return "Composite({0}, {1})".format(self.__uid, self.__name)

# ------------------------------------------------------------------------------

class Component(object):
    """
    Represents a component
    """
    def __init__(self, name, factory, properties, uid=None):
        """
        Sets up the composite
        
        :param name: Name of the component
        :param factory: Factory of the component
        :param properties: Component properties
        :param uid: Component instance UID (None for the parser)
        :raise ValueError: Invalid parameters
        """
        if not factory:
            raise ValueError("Factory can't be empty")

        if not name:
            raise ValueError("Name can't be empty")

        if '.' in name:
            raise ValueError("A component name can't contain a '.' (dot)")

        # Read-only parameters
        self.__uid = uid
        self.__factory = factory
        self.__name = name
        self.__preferred_isolate = None
        self.__preferred_node = None

        # Original component bean (for copied elements)
        self.__original = None

        # Set-once parameter
        self.__fullname = None
        self.__language = None

        # Configured properties
        self.__properties = properties.copy() if properties else {}

        # Wires: Field name -> Component name
        self._wires = {}

        # Filters: Field name -> LDAP Filter
        self._filters = {}


    def as_dict(self):
        """
        Converts the bean into a dictionary
        """
        return {"uid": self.__uid,
                "name": self.__fullname,
                "type": self.__factory,
                # Parent name: full name without '.name'
                "parentName": self.fullname[:-(len(self.__name) + 1)],
                "fieldsFilters": self._filters,
                "properties": self.__properties,
                "isolate": self.__preferred_isolate,
                "node": self.__preferred_node
                }


    @property
    def uid(self):
        """
        The UID of the component
        """
        return self.__uid


    @property
    def factory(self):
        """
        The factory of the component
        """
        return self.__factory


    @property
    def name(self):
        """
        The name of the component instance
        """
        return self.__name


    @property
    def properties(self):
        """
        The configured properties
        """
        return self.__properties


    @property
    def original(self):
        """
        The original configuration bean
        """
        if self.__original is None:
            # Return this configuration bean
            return self

        else:
            # Return the original configuration bean
            return self.__original


    @property
    def isolate(self):
        """
        The preferred isolate to host this component
        """
        return self.__preferred_isolate


    @isolate.setter
    def isolate(self, isolate):
        """
        The preferred isolate to host this component
        """
        self.__preferred_isolate = isolate


    @property
    def node(self):
        """
        The preferred node to host this component
        """
        return self.__preferred_node


    @node.setter
    def node(self, node):
        """
        The preferred node to host this component
        """
        self.__preferred_node = node


    @property
    def fullname(self):
        """
        The component full name
        """
        return self.__fullname


    @fullname.setter
    def fullname(self, name):
        """
        Sets the component full name if it is not yet set.
        """
        if not self.__fullname:
            self.__fullname = name


    @property
    def language(self):
        """
        The component implementation language
        """
        return self.__language


    @language.setter
    def language(self, language):
        """
        Sets the component implementation language
        """
        if not self.__language:
            self.__language = language


    def link_wires(self, composite):
        """
        Converts the wires into filters
        
        :param composite: The composite calling this method
        :return: True if all wires have been linked
        """
        result = True

        for field, name in self._wires.items():
            target = composite.find_component(name)
            if target:
                # Target found: escape its name
                name = ldapfilter.escape_LDAP(name)

                # Make the wire filter
                wire_filter = "(instance.name={0})".format(name)

                # Get the previous filter
                field_filter = self._filters.get(field)
                if field_filter:
                    # A filter already exists: combine with the new one
                    field_filter = ldapfilter.combine_filters([field_filter,
                                                               wire_filter])
                # Store it
                self._filters[field] = str(field_filter)

            else:
                # A wire can't be linked (continue)
                result = False

        return result


    def set_filter(self, field, ldap_filter):
        """
        Sets a configured filter for the given field (replaces previous filter).
        Removes the custom filter if ldap_filter is None
        
        :param field: Name of a filtered field
        :param ldap_filter: LDAP filter to use
        :return: The previous filter, or None
        :raise KeyError: Invalid field name
        :raise ValueError: Invalid LDAP filter
        """
        if not field:
            raise KeyError("No field given")

        # Keep the previous filter
        previous = self._filters.get(field)

        if ldap_filter is None:
            # None filter: remove the entry
            if field in self._filters:
                del self._filters[field]

        elif not ldap_filter:
            # Empty filter: store it
            self._filters[field] = ""

        else:
            # Filter given, parse it (might raise an error)
            parsed_filter = ldapfilter.get_ldap_filter(ldap_filter)

            # Store its string representation
            if parsed_filter is not None:
                self._filters[field] = str(parsed_filter)

        return previous


    def set_wire(self, field, wire):
        """
        Sets a configured wire for the given field (replaces previous wire).
        Removes the custom wire if wire is empty.
        
        :param field: Name of a wired field
        :param wire: Name of the wired component 
        :return: The previous wire, or None
        :raise KeyError: Invalid field name
        """
        if not wire:
            raise KeyError("No wire given")

        # Keep the previous value
        previous = self._wires.get(field)

        if not wire:
            # Remove the wire
            if field in self._wires:
                del self._wires[field]

        else:
            # Store it: wire validation will be done at resolution time
            self._wires[field] = wire

        return previous


    def copy(self, uid):
        """
        Makes a copy this bean, with the given UID.
        Only original beans can be copied
        
        :param uid: UID of the copy of this bean
        :return: A copy of this bean
        :raise TypeError: Only original beans can be copied
        :raise ValueError: Invalid UID
        """
        if self.__uid is not None:
            raise TypeError("Can't make a copy of a non-original bean")

        if not uid:
            raise ValueError("No UID given")
        else:
            uid = str(uid)

        # New component
        copy = Component(self.__name, self.__factory, self.__properties, uid)

        # Add a reference to the original
        copy.__original = self

        # Copy other members
        copy._filters = self._filters.copy()
        copy._wires = self._wires.copy()

        copy.__fullname = self.__fullname
        copy.__language = self.__language
        copy.__preferred_isolate = self.__preferred_isolate
        copy.__preferred_node = self.__preferred_node

        return copy


    def __repr__(self):
        """
        String representation of the composition
        """
        return "Component({0}, {1}, {2}, {3})".format(self.__name,
                                                      self.__factory,
                                                      self.__properties,
                                                      self.__uid
                                                      or "<original>")
