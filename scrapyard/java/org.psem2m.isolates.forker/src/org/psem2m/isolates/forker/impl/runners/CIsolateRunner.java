/**
 * File:   CIsolateRunner.java
 * Author: Thomas Calmant
 * Date:   7 juil. 2011
 */
package org.psem2m.isolates.forker.impl.runners;

import java.io.File;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.apache.felix.ipojo.annotations.Component;
import org.apache.felix.ipojo.annotations.Instantiate;
import org.apache.felix.ipojo.annotations.Invalidate;
import org.apache.felix.ipojo.annotations.Provides;
import org.apache.felix.ipojo.annotations.Requires;
import org.apache.felix.ipojo.annotations.Validate;
import org.osgi.framework.BundleException;
import org.psem2m.isolates.base.IIsolateLoggerSvc;
import org.psem2m.isolates.base.Utilities;
import org.psem2m.isolates.base.activators.CPojoBase;
import org.psem2m.isolates.base.bundles.BundleRef;
import org.psem2m.isolates.base.bundles.IBundleFinderSvc;
import org.psem2m.isolates.constants.IPlatformProperties;
import org.psem2m.isolates.constants.boot.IBootstrapConstants;
import org.psem2m.isolates.forker.IIsolateRunner;
import org.psem2m.isolates.forker.IProcessRef;
import org.psem2m.isolates.services.conf.beans.IsolateDescription;
import org.psem2m.isolates.services.dirs.IPlatformDirsSvc;

/**
 * OSGi framework isolate runner
 * 
 * @author Thomas Calmant
 */
@Component(name = "psem2m-runner-osgi-factory", publicFactory = false)
@Provides(specifications = IIsolateRunner.class)
@Instantiate(name = "psem2m-runner-osgi")
public class CIsolateRunner extends CPojoBase implements IIsolateRunner {

    /** Equinox framework names */
    public static final String[] EQUINOX_NAMES = new String[] {
            "org.eclipse.osgi", "org.eclipse.osgi_3.7.0.v20110613.jar",
            "equinox.jar" };

    /** Felix framework names */
    public static final String[] FELIX_NAMES = new String[] {
            "org.apache.felix.main", "org.apache.felix.main-3.2.2.jar",
            "felix.jar" };

    /** Bootstrap long argument prefix */
    public static final String LONG_ARGUMENT_PREFIX = "--";

    /** Supported isolate kinds */
    public static final Map<String, String[]> SUPPORTED_ISOLATE_KINDS = new HashMap<String, String[]>();

    /*
     * Map initialization
     */
    static {
        SUPPORTED_ISOLATE_KINDS.put("felix", FELIX_NAMES);
        SUPPORTED_ISOLATE_KINDS.put("equinox", EQUINOX_NAMES);
    }

    /** Base debug port, <= 0 if not used */
    private int pBaseDebugPort = -1;

    /** Bundle finder service, injected by iPOJO */
    @Requires
    private IBundleFinderSvc pBundleFinderSvc;

    /** Launched isolate index */
    private int pIsolateIndex = 0;

    /** The logger service, injected by iPOJO */
    @Requires
    private IIsolateLoggerSvc pIsolateLoggerSvc;

    /** Java isolate runner service, injected by iPOJO */
    @Requires
    private IJavaRunner pJavaRunnerSvc;

    /** The platform directory service, injected by iPOJO */
    @Requires
    private IPlatformDirsSvc pPlatformDirsSvc;

    /**
     * Converts an array of bundle references to an URL list. Ignores invalid
     * names.
     * 
     * @param aBundles
     *            Bundles to be converted.
     * @return A list of URLs
     */
    protected List<URL> bundlesToUrls(final BundleRef[] aBundles) {

        final List<URL> bundleURLs = new ArrayList<URL>();

        // Loop on bundles
        for (final BundleRef bundleRef : aBundles) {
            try {
                final URL bundleUrl = bundleRef.getUri().toURL();
                bundleURLs.add(bundleUrl);

            } catch (final MalformedURLException e) {
                e.printStackTrace();
            }
        }

        return bundleURLs;
    }

    /*
     * (non-Javadoc)
     * 
     * @see org.psem2m.isolates.forker.IIsolateRunner#canRun(java.lang.String)
     */
    @Override
    public boolean canRun(final String aIsolateKind) {

        return SUPPORTED_ISOLATE_KINDS.keySet().contains(aIsolateKind);
    }

    /*
     * (non-Javadoc)
     * 
     * @see org.psem2m.isolates.base.CPojoBase#invalidatePojo()
     */
    @Override
    @Invalidate
    public void invalidatePojo() throws BundleException {

        // logs in the bundle logger
        pIsolateLoggerSvc.logInfo(this, "invalidatePojo", "INVALIDATE",
                toDescription());
    }

    /**
     * Prepares a property definition as a bootstrap program argument
     * 
     * @param aKey
     *            Property name
     * @param aValue
     *            Property value
     * @return The property definition as a bootstrap argument
     */
    protected String makeBootstrapDefinition(final String aKey,
            final String aValue) {

        final StringBuilder bootstrapDef = new StringBuilder(aKey.length()
                + aValue.length() + 1);
        bootstrapDef.append(aKey);
        bootstrapDef.append("=");
        bootstrapDef.append(aValue);

        return bootstrapDef.toString();
    }

    /**
     * Prepares bootstrap arguments. Indicates the kind of framework to be used
     * and sets up isolate properties.
     * 
     * @param aIsolateConfiguration
     *            Description of the isolate
     * 
     * @return The bootstrap arguments, never null
     */
    protected List<String> prepareBootstrapArguments(
            final IsolateDescription aIsolateConfiguration) {

        final List<String> bootstrapArguments = new ArrayList<String>();

        // Framework to be used (in lower case)
        bootstrapArguments.add(makeBootstrapDefinition(
                IBootstrapConstants.CONFIG_FRAMEWORK, aIsolateConfiguration
                        .getKind().toString().toLowerCase()));

        // Isolate ID
        bootstrapArguments.add(makeBootstrapDefinition(
                IPlatformProperties.PROP_PLATFORM_ISOLATE_ID,
                aIsolateConfiguration.getId()));

        // PSEM2M Home
        bootstrapArguments.add(makeBootstrapDefinition(
                IPlatformProperties.PROP_PLATFORM_HOME, pPlatformDirsSvc
                        .getPlatformHomeDir().getAbsolutePath()));

        // PSEM2M Base
        bootstrapArguments.add(makeBootstrapDefinition(
                IPlatformProperties.PROP_PLATFORM_BASE, pPlatformDirsSvc
                        .getPlatformBaseDir().getAbsolutePath()));

        return bootstrapArguments;
    }

    /**
     * Prepares the JVM classpath argument according to the isolate kind
     * 
     * @param aBootstrapFile
     *            The bootstrap JAR file
     * 
     * @return the JVM classpath argument
     */
    protected List<String> prepareClasspathArgument(final File aBootstrapFile,
            final String aKind) {

        final List<String> classpathArgument = new ArrayList<String>();
        classpathArgument.add("-cp");

        // Don't forget the current directory as a classpath
        final StringBuilder classPath = new StringBuilder();

        // Find the framework main bundle
        BundleRef mainBundleRef;

        String[] mainBundleNames = SUPPORTED_ISOLATE_KINDS.get(aKind);
        if (mainBundleNames == null) {
            // Use Felix framework by default, we should never come here
            mainBundleNames = FELIX_NAMES;

            pIsolateLoggerSvc
                    .logWarn(this, "prepareClasspathArgument",
                            "Unsupported isolate kind, using the Felix framework by default");
        }

        mainBundleRef = pBundleFinderSvc.findBundle(mainBundleNames);
        if (mainBundleRef == null || mainBundleRef.getFile() == null) {
            pIsolateLoggerSvc.logSevere(this, "prepareClasspathArgument",
                    "Can't find an OSGi framework file, searching for : "
                            + Arrays.toString(mainBundleNames));
            return null;
        }

        // Add the bootstrap JAR
        classPath.append(aBootstrapFile.getAbsolutePath());
        classPath.append(File.pathSeparator);

        // Add the OSGi framework
        classPath.append(mainBundleRef.getFile().getAbsolutePath());
        classPath.append(File.pathSeparator);

        classPath.append(".");
        classpathArgument.add(classPath.toString());
        return classpathArgument;
    }

    /**
     * Sets up the debug mode members
     */
    protected void prepareDebugMode() {

        // Test if the debug port is indicated
        final String debugPortStr = System
                .getProperty(IPlatformProperties.PROP_BASE_DEBUG_PORT);
        if (debugPortStr == null) {
            return;
        }

        // Prepare the base port to be used
        try {
            pBaseDebugPort = Integer.parseInt(debugPortStr);

            if (pBaseDebugPort <= 0 || pBaseDebugPort > 65535) {
                throw new NumberFormatException("Invalid port number");
            }

        } catch (final NumberFormatException ex) {

            // Reset the port value, if needed
            pBaseDebugPort = -1;

            pIsolateLoggerSvc.logWarn(this, "prepareDebugMode",
                    "Can't activate Debug Mode, invalide port number : ",
                    debugPortStr);
        }
    }

    /**
     * Prepares the debug mode parameters, if needed
     * 
     * @param aJavaOptions
     *            Java program arguments (before -jar)
     */
    protected void setupDebugMode(final List<String> aJavaOptions) {

        if (aJavaOptions == null || pBaseDebugPort <= 0) {
            return;
        }

        // JVM debug mode
        aJavaOptions.add("-Xdebug");

        // Connection parameter
        aJavaOptions.add(String.format(
                "-Xrunjdwp:transport=dt_socket,address=127.0.0.1:%d,suspend=y",
                pBaseDebugPort + pIsolateIndex));
    }

    /*
     * (non-Javadoc)
     * 
     * @see
     * org.psem2m.isolates.forker.IIsolateRunner#startIsolate(org.psem2m.isolates
     * .base.conf.IIsolateDescr)
     */
    @Override
    public IProcessRef startIsolate(
            final IsolateDescription aIsolateConfiguration) throws Exception {

        final List<String> javaOptions = new ArrayList<String>();

        // A new isolate is launched
        pIsolateIndex++;

        // Find the bootstrap JAR file
        final File bootstrapFile = pBundleFinderSvc.getBootstrap();

        // Add the class path argument
        final List<String> classpath = prepareClasspathArgument(bootstrapFile,
                aIsolateConfiguration.getKind());
        if (classpath == null) {
            // Error preparing the classpath argument
            return null;
        }

        javaOptions.addAll(classpath);

        // Set debug mode, if needed
        setupDebugMode(javaOptions);

        // Add isolate VM arguments
        javaOptions.addAll(aIsolateConfiguration.getVmArgs());

        // Add the Bootstrap main class name
        javaOptions.add(IBundleFinderSvc.BOOTSTRAP_MAIN_CLASS);

        // Add its arguments
        javaOptions.addAll(prepareBootstrapArguments(aIsolateConfiguration));

        // Set up the working directory
        final File workingDirectory = pPlatformDirsSvc
                .getIsolateWorkingDir(aIsolateConfiguration.getId());

        // Create the working directory
        if (workingDirectory.exists()) {
            Utilities.removeDirectory(workingDirectory);
        }
        workingDirectory.mkdirs();

        // Run the bootstrap
        return pJavaRunnerSvc.runJava(javaOptions, null, workingDirectory);
    }

    /*
     * (non-Javadoc)
     * 
     * @see org.psem2m.isolates.base.CPojoBase#validatePojo()
     */
    @Override
    @Validate
    public void validatePojo() throws BundleException {

        // Read debug properties
        prepareDebugMode();

        // logs in the bundle logger
        pIsolateLoggerSvc.logInfo(this, "validatePojo", "VALIDATE",
                toDescription());
    }
}