#!/usr/bin/env python
# -- Content-Encoding: UTF-8 --
"""
COHORTE Java Virtual Machine loader

Loads a JVM in the current process using jPype.

**WARNING:** Only one (1) JVM can be loaded in a process, ever; i.e. if you
kill the JVM, you must start the next one a new process.

:author: Thomas Calmant
:license: GPLv3
"""

# Documentation strings format
__docformat__ = "restructuredtext en"

# Boot module version
__version__ = "1.0.0"

# ------------------------------------------------------------------------------

# COHORTE modules
import cohorte

# iPOPO Decorators
from pelix.ipopo.decorators import ComponentFactory, Provides, Validate, \
    Invalidate

# jPype
import jpype

# Python standard library
import logging
import os

# ------------------------------------------------------------------------------

PROP_JVM_LOADED = 'cohorte.java.loaded'
"""
Once this framework property is True, no other JVM can be loaded in the current
process
"""

_logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------

@ComponentFactory('cohorte-java-runner-factory')
@Provides(cohorte.SERVICE_JAVA_RUNNER)
class JavaVM(object):
    """
    Forker isolate loader component. Automatically instantiated.
    """
    def __init__(self):
        """
        Sets up members
        """
        # Bundle context
        self._context = None

        # JVM presence flag
        self._jvm_running = False


    def add_jar(self, jar_file_path):
        """
        Adds a JAR in the JVM class path
        
        :param jar_file_path: Path to the JAR file to add
        :raise KeyError: No JVM is loaded
        :raise ValueError: Error loading the JAR file
        """
        if not self._context.get_property(PROP_JVM_LOADED):
            raise KeyError("JVM not loaded yet.")

        try:
            # Java classes
            File = self.load_class('java.util.File')
            ClassLoader = self.load_class('java.lang.ClassLoader')

            # Code from:
            # http://jimlife.wordpress.com/2007/12/19/java-adding-new-classpath-at-runtime/
            jar_file = File(jar_file_path)
            jar_url = jar_file.toURL()

            # jPype will do the reflection stuffs for us
            class_loader = ClassLoader.getSystemClassLoader();
            class_loader.addURL(jar_url)

        except jpype.JavaException as ex:
            raise ValueError("Error loading the JAR file '{0}': {1}" \
                             .format(jar_file, ex))


    def get_package(self, name):
        """
        Retrieves the wrapper for the given Java package.
        
        Having a result doesn't mean that the package name is correct.
        
        :param name: A Java package name
        :return: The wrapper for this package
        """
        return jpype.JPackage(name)


    def is_running(self):
        """
        Tests if the JVM is currently running
        
        :return: True if the JVM is running
        """
        return self._jvm_running


    def load_class(self, name):
        """
        Loads the given class from the JVM
        
        :param name: A Java class name
        :return: The wrapper for this Java class
        :raise ValueError: The class couldn't be loaded
        """
        try:
            return jpype._jclass.JClass(name)

        except jpype.JavaException as ex:
            raise ValueError(str(ex))


    def make_proxy(self, instance, interface=None):
        """
        Makes a proxy to be able to use the given instance in the Java world.
        Only the given interface methods will be visible in the Java world.
        
        If no interface is given, this method will look for the JAVA_INTERFACE
        member of the instance, and raise a KeyError exception if it is
        missing.
        
        :param instance: A Python object instance
        :param interface: A Java interface name
        :return: The Java instance proxy
        :raise KeyError: No Java interface given
        :raise Exception: Error on Java side
        """
        if interface is None:
            interface = getattr(instance, 'JAVA_INTERFACE', None)

        if interface is None:
            raise KeyError("No Java interface given")

        return jpype.JProxy(interface, inst=instance)


    def make_jvm_classpath(self, classpath):
        """
        Prepares the arguments of the JVM
        
        :param classpath: A list of files in the class path
        :return: The corresponding class path argument
        """
        return "-Djava.class.path={0}".format(os.path.pathsep.join(classpath))


    def make_jvm_property(self, key, value):
        """
        Formats a JVM property definition (-Dkey=value)
        
        :param key: Property key
        :param value: Property value
        :return: The property definition
        """
        return "-D{0}={1}".format(key, value)


    def start(self, vm_library=None, *args):
        """
        Starts a JVM with the given parameters
        
        :raise KeyError: A JVM is already running
        :raise ValueError: Invalid parameter
        """
        if self._context.get_property(PROP_JVM_LOADED):
            raise KeyError("A JVM has already been loaded in this process.")

        # Get the JVM library path
        if not vm_library:
            vm_library = jpype.getDefaultJVMPath()

        # Load the JVM
        jpype.startJVM(vm_library, *args)

        # Update the presence flag
        self._context.get_bundle(0).add_property(PROP_JVM_LOADED, True)
        self._jvm_running = True


    def stop(self):
        """
        Stops the JVM.
        
        :return: True if the JVM has been stopped, else False
        """
        if self._jvm_running:
            # Update the presence flag
            self._jvm_running = False

            # Stop the JVM
            jpype.shutdownJVM()


    @Validate
    def validate(self, context):
        """
        Component validated
        
        :param context: The bundle context
        """
        # Store the framework access
        self._context = context


    @Invalidate
    def invalidate(self, context):
        """
        Component invalidated
        
        :param context: The bundle context
        """
        # Stop the JVM
        self.stop()

        # Clear the framework access
        self._context = None