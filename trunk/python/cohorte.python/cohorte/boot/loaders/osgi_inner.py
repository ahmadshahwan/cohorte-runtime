#!/usr/bin/env python
# -- Content-Encoding: UTF-8 --
"""
COHORTE Java isolate loader

**TODO:*
* Review constants names & values

:author: Thomas Calmant
:license: GPLv3
"""

# Documentation strings format
__docformat__ = "restructuredtext en"

# Version
__version__ = '1.0.0'

# ------------------------------------------------------------------------------

# COHORTE constants
import cohorte.repositories

# iPOPO Decorators
from pelix.ipopo.decorators import ComponentFactory, Provides, Validate, \
    Invalidate, Property, Requires
import pelix.framework
import pelix.shell

# Python standard library
import logging
import os

# ------------------------------------------------------------------------------

ISOLATE_LOADER_FACTORY = 'cohorte-loader-java-factory'
""" Forker loader factory name """

LOADER_KIND = 'osgi'
""" Kind of isolate started with this loader """

BUNDLE_SERVICES_FOLDER = 'META-INF/services'
""" Path of the descriptions of the bundle services (in a JAR) """

FRAMEWORK_SERVICE = 'org.osgi.framework.launch.FrameworkFactory'
""" FrameworkFactory service descriptor in the framework JAR file """

FRAMEWORK_SYSTEMPACKAGES_EXTRA = "org.osgi.framework.system.packages.extra"
""" OSGi extra system packages """

PYTHON_BRIDGE_BUNDLE_API = "org.cohorte.pyboot.api"
""" Name of the Python bridge API bundle """

PYTHON_BRIDGE_BUNDLE = "org.cohorte.pyboot"
""" Name of the Python bridge bundle """

PYTHON_JAVA_BRIDGE_INTERFACE = "org.cohorte.pyboot.api.IPyBridge"
""" Interface of the Python - Java bridge """

_logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------

class PyBridge(object):
    """
    Python - Java bridge service implementation
    """
    # Implemented Java interface
    JAVA_INTERFACE = PYTHON_JAVA_BRIDGE_INTERFACE

    def __init__(self, context, jvm, java_configuration, configuration_parser,
                 callback):
        """
        Sets up the bridge
        
        :param context: The bundle context
        :param jvm: The JVM wrapper
        :param java_configuration: Java boot configuration
        :param callback: Method to call back on error or success
        """
        # Bundle context
        self._context = context

        # Java class
        self.ArrayList = jvm.load_class("java.util.ArrayList")
        self.Component = jvm.load_class("org.cohorte.pyboot.api.ComponentBean")
        self.HashMap = jvm.load_class("java.util.HashMap")

        # Prepare members
        self._callback = callback
        self._components = {}
        self._parser = configuration_parser

        # Convert stored components
        self._java_boot_config = self._to_java(java_configuration)
        self._prepare_components(java_configuration.composition)


    def _prepare_components(self, raw_components):
        """
        Converts the Python Component objects into Java Component beans
        
        :param raw_components: Python components representations
        """
        for component in raw_components:
            # Convert properties
            properties = self.HashMap()
            for key, value in component.properties.items():
                properties.put(key, value)

            # Store the component bean
            self._components[component.name] = self.Component(component.factory,
                                                              component.name,
                                                              properties)

    def _to_java(self, data):
        """
        Recursively converts lists and maps to Java ones
        
        :param data: Data to be converted
        :return: Converted data
        """
        if hasattr(data, '_asdict'):
            # Named tuple
            data = data._asdict()

        if isinstance(data, dict):
            # Convert a dictionary
            converted = self.HashMap()

            for key, value in data.items():
                # Convert entry
                new_key = self._to_java(key)
                new_value = self._to_java(value)

                converted.put(new_key, new_value)

            # Return the new value
            return converted

        elif isinstance(data, (list, tuple, set)):
            # Convert a list
            converted = self.ArrayList()

            for item in data:
                # Convert each item
                converted.add(self._to_java(item))

            return converted

        else:
            # No conversion
            return data


    def debug(self, message, values):
        """
        Logs a debug message
        """
        _logger.debug(message.format(*values))


    def error(self, message, values):
        """
        Logs an error message
        """
        _logger.error(message.format(*values))


    def getComponents(self):
        """
        Retrieves the components to instantiate (Java API)
        
        :return: An array of components
        """
        # Create a list
        result = self.ArrayList()
        for component in self._components.values():
            result.add(component)

        return result


    def getStartConfiguration(self):
        """
        Retrieves the configuration used to start this isolate as a map
        
        :return: The configuration used to start this isolate
        """
        return self._java_boot_config


    def getPid(self):
        """
        Retrieves the Process ID of this isolate
        
        :return: The isolate PID
        """
        return os.getpid()


    def getRemoteShellPort(self):
        """
        Returns the port used by the Pelix remote shell, or -1 if the shell is
        not active
        
        :return: The port used by the remote shell, or -1
        """
        ref = self._context.get_service_reference(pelix.shell.REMOTE_SHELL_SPEC)
        if ref is None:
            return -1

        try:
            # Get the service
            shell = self._context.get_service(ref)

            # Get the shell port
            port = shell.get_access()[1]

            # Release the service
            self._context.unget_service(ref)

            return port

        except pelix.framework.BundleException:
            # Service lost (called while the framework was stopping)
            return -1


    def onComponentStarted(self, name):
        """
        Called when a component has been started
        
        :param name: Name of the started component
        """
        if name in self._components:
            del self._components[name]

        if not self._components:
            self._callback(True, "All components have been instantiated")


    def onError(self, error):
        """
        Called when an error has occurred
        
        :param error: An error message
        """
        self._callback(False, error)


    def prepareIsolate(self, uid, name, node, kind, level, sublevel,
                       bundles, composition):
        """
        Prepares the configuration dictionary of an isolate
        """
        try:
            conf = self._parser.prepare_isolate(uid, name, node, kind,
                                                level, sublevel,
                                                bundles, composition)

        except:
            _logger.exception("Error preparing isolate...")
            return None

        return self._to_java(conf)


    def readConfiguration(self, filename):
        """
        Reads the given configuration file
        
        :param filename: A configuration file name
        :return: The parsed configuration map
        """
        # Load the file
        raw_dict = self._parser.read(filename)

        # Convert the dictionary to Java
        return self._to_java(raw_dict)

# ------------------------------------------------------------------------------

@ComponentFactory(ISOLATE_LOADER_FACTORY)
@Provides(cohorte.SERVICE_ISOLATE_LOADER)
@Property('_handled_kind', cohorte.SVCPROP_ISOLATE_LOADER_KIND, LOADER_KIND)
@Requires('_java', cohorte.SERVICE_JAVA_RUNNER)
@Requires('_repository', cohorte.repositories.SERVICE_REPOSITORY_ARTIFACTS,
          spec_filter="({0}=java)" \
                      .format(cohorte.repositories.PROP_REPOSITORY_LANGUAGE))
@Requires('_config', cohorte.SERVICE_CONFIGURATION_READER)
@Requires('_finder', cohorte.SERVICE_FILE_FINDER)
class JavaOsgiLoader(object):
    """
    Pelix isolate loader. Needs a configuration to be given as a parameter of
    the load() method.
    """
    def __init__(self):
        """
        Sets up members
        """
        # Injected services
        self._java = None
        self._config = None
        self._finder = None
        self._repository = None

        # Pelix bundle context
        self._context = None

        # OSGi Framework
        self._osgi = None

        # Bridge service registration
        self._bridge_reg = None


    def _setup_vm_properties(self, properties):
        """
        Sets up the JVM system properties dictionary (not the arguments)
        
        :param properties: Configured properties
        :return: VM properties dictionary
        """
        # Prepare the dictionary
        if properties:
            return properties.copy()

        return {}


    def _setup_osgi_properties(self, properties, allow_bridge):
        """
        Sets up the OSGi framework properties and converts them into a Java
        HashMap.
        
        :param properties: Configured framework properties
        :param allow_bridge: If True, the bridge API package will be exported
                             by the framework.
        :return: The framework properties as a Java Map
        """
        osgi_properties = self._java.load_class("java.util.HashMap")()
        for key, value in properties.items():
            if value is not None:
                osgi_properties.put(key, str(value))

        # Inherit some Pelix properties
        for key in (cohorte.PROP_HOME, cohorte.PROP_BASE,
                    cohorte.PROP_UID, cohorte.PROP_NAME, cohorte.PROP_NODE,
                    cohorte.PROP_DUMPER_PORT):
            value = self._context.get_property(key)
            if value is not None:
                # Avoid empty values
                osgi_properties.put(key, str(value))

        if allow_bridge:
            # Prepare the "extra system package" framework property
            osgi_properties.put(FRAMEWORK_SYSTEMPACKAGES_EXTRA,
                                "{0}; version=1.0.0" \
                                .format(PYTHON_BRIDGE_BUNDLE_API))

        return osgi_properties


    def _start_jvm(self, vm_args, classpath, properties):
        """
        Starts the JVM, with the given file in the class path
        
        :param vm_args: JVM arguments
        :param classpath: A list of JAR files
        :param properties: Java system properties
        :raise KeyError: Error starting the JVM
        :raise ValueError: Invalid JAR file
        """
        # Start a JVM if necessary
        if not self._java.is_running():
            # Arguments given to the Java runner
            java_args = []

            if vm_args:
                # VM specific arguments first
                java_args.extend(vm_args)

            # Set the class path as a parameter
            java_args.append(self._java.make_jvm_classpath(classpath))

            # Prepare the JVM properties definitions
            for key, value in self._setup_vm_properties(properties).items():
                java_args.append(self._java.make_jvm_property(key, value))

            self._java.start(None, *java_args)

        else:
            # Add the JAR to the class path
            for jar_file in classpath:
                self._java.add_jar(jar_file)


    def _close_osgi(self):
        """
        Stops the OSGi framework and clears all references to it
        """
        # Unregister services
        if self._bridge_reg is not None:
            self._bridge_reg.unregister()
            self._bridge_reg = None

        # Stop the framework
        if self._osgi is not None:
            self._osgi.stop()
            self._osgi = None


    def _register_bridge(self, context, java_configuration):
        """
        Instantiates and starts the iPOJO components instantiation handler
        
        :param context: An OSGi bundle context
        :param java_configuration: The Java boot configuration
        """
        # Make a Java proxy of the bridge
        bridge_java = self._java.make_proxy(PyBridge(self._context,
                                                     self._java,
                                                     java_configuration,
                                                     self._config,
                                                     self._bridge_callback))

        # Register it to the framework
        self._bridge_reg = context.registerService(PyBridge.JAVA_INTERFACE,
                                                   bridge_java, None)


    def _bridge_callback(self, success, message):
        """
        Called back by the Python-Java bridge
        
        :param success: If True, all components have been started, else an error
                        occurred
        :param message: A call back message
        """
        if success:
            _logger.debug("Bridge success: %s", message)

        else:
            _logger.warning("Bridge error: %s", message)


    def _find_osgi_jar(self, osgi_jar, symbolic_name):
        """
        Looks for the OSGi framework JAR file matching the given parameters
        
        :param osgi_jar: An OSGi framework JAR file name
        :param symbolic_name: An OSGi framework symbolic name
        :return: A (file name, framework factory) tuple
        :raise ValueError: No OSGi framework found
        """
        try:
            # We've been given a specific JAR file or symbolic name
            osgi_bundle = self._repository.get_artifact(symbolic_name,
                                                        filename=osgi_jar)

        except ValueError:
            # Bundle not found
            for bundle in self._repository.filter_services(FRAMEWORK_SERVICE):
                # Get the first found framework
                osgi_bundle = bundle
                break

            else:
                # No match found
                raise ValueError("No OSGi framework found in repository")

        # Found !
        return osgi_bundle.file, osgi_bundle.get_service(FRAMEWORK_SERVICE)


    def load(self, configuration):
        """
        Loads the Java OSGi isolate
        
        :param configuration: Isolate configuration dictionary (required)
        :raise KeyError: A mandatory property is missing
        :raise ValueError: Invalid parameter/file encountered or the JVM
                           can't be loaded
        :raise BundleException: Error installing a bundle
        :raise Exception: Error instantiating a component
        """
        if not configuration:
            raise KeyError("A configuration is required to load a "
                           "Java OSGi isolate")

        # Parse the configuration (boot-like part) -> Might raise error
        java_config = self._config.load_boot_dict(configuration)

        # Find the OSGi JAR file to use
        osgi_jar_file, factory_name = self._find_osgi_jar(
                                              configuration.get('osgi_jar'),
                                              configuration.get('osgi_name'))

        _logger.debug("Using OSGi JAR file: %s", osgi_jar_file)

        # Prepare the VM arguments
        classpath = [osgi_jar_file]

        # Find the bridge API JAR file
        api_jar = self._repository.get_artifact(PYTHON_BRIDGE_BUNDLE_API)
        if api_jar:
            # Add the bundle to the class path...
            classpath.append(api_jar.file)
        else:
            _logger.warning("No Python bridge API bundle found")


        # Start the JVM
        _logger.debug("Starting JVM...")
        self._start_jvm(configuration.get('vm_args'), classpath,
                        configuration.get('vm_properties'))

        # Load the FrameworkFactory implementation
        FrameworkFactory = self._java.load_class(factory_name)
        factory = FrameworkFactory()

        # Framework properties
        osgi_properties = self._setup_osgi_properties(java_config.properties,
                                                      api_jar is not None)

        # Start a framework, with the given properties
        self._osgi = factory.newFramework(osgi_properties)
        self._osgi.start()
        context = self._osgi.getBundleContext()

        # Install bundles
        java_bundles = []

        # Install the bridge
        bundle = self._repository.get_artifact(PYTHON_BRIDGE_BUNDLE)
        if not bundle:
            _logger.warning("No Python bridge bundle found")

        else:
            java_bundles.append(context.installBundle(bundle.url))

        # Install the configured bundles
        for bundle_conf in java_config.bundles:
            bundle = self._repository.get_artifact(bundle_conf.name,
                                                   bundle_conf.version,
                                                   bundle_conf.filename)
            if bundle:
                _logger.debug("Installing Java bundle %s...", bundle.name)
                java_bundles.append(context.installBundle(bundle.url))

            elif not bundle_conf.optional:
                raise ValueError("Bundle not found: {0}".format(bundle_conf))

            else:
                _logger.warning("Bundle not found: %s", bundle_conf)

        # Start the bundles
        for bundle in java_bundles:
            _logger.debug("Starting %s...", bundle.getSymbolicName())
            bundle.start()

        # Start the component instantiation handler
        self._register_bridge(context, java_config)


    def wait(self):
        """
        Waits for the isolate to stop
        """
        if not self._osgi:
            # Nothing to do
            return

        # Wait for the OSGi framework to stop
        try:
            self._osgi.waitForStop(0)

        except Exception as ex:
            _logger.exception("Error waiting for the OSGi framework "
                              "to stop: %s", ex)
            raise


    @Validate
    def validate(self, context):
        """
        Component validated
        
        :param context: The bundle context
        """
        # Update the finder
        self._finder.update_roots()

        # Store the framework access
        self._context = context


    @Invalidate
    def invalidate(self, context):
        """
        Component invalidated
        
        :param context: The bundle context
        """
        # Stop the framework
        self._close_osgi()

        # Clear the JVM
        self._java.stop()

        # Clear the framework access
        self._context = None
