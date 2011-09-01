/**
 * File:   BootstrapRunner.java
 * Author: Thomas Calmant
 * Date:   24 août 2011
 */
package org.psem2m.eclipse.runner.work;

import java.io.File;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;

import org.eclipse.core.runtime.CoreException;
import org.eclipse.debug.core.DebugPlugin;
import org.eclipse.debug.core.ILaunch;
import org.psem2m.eclipse.runner.RunnerPlugin;

/**
 * Runs the PSEM2M bootstrap with debug options
 * 
 * @author Thomas Calmant
 */
public class PlatformRunner {

	/** PSEM2M Base */
	private File pBase;

	/** Base remote debug port */
	private int pBaseDebugPort;

	/** PSEM2M Home */
	private File pHome;

	/** Working directory */
	private File pWorkingDirectory;

	/**
	 * Sets up the bootstrap runner
	 * 
	 * @param aPlatformHome
	 *            PSEM2M Home
	 * 
	 * @param aPlatformBase
	 *            PSEM2M Base
	 * 
	 * @param aBaseDebugPort
	 *            Base remote debug port
	 */
	public PlatformRunner(final File aPlatformHome, final File aPlatformBase,
			final File aWorkingDir, final int aBaseDebugPort) {

		// Store the port
		pBaseDebugPort = aBaseDebugPort;

		// Prepare home and base directories
		pHome = aPlatformHome;
		if (pHome == null) {
			// Use a default value here
			pHome = new File(System.getProperty("user.home"));
		}

		pBase = aPlatformBase;
		if (pBase == null) {
			// Use home as base if needed
			pBase = pHome;
		}

		// Prepare working directory
		pWorkingDirectory = aWorkingDir;
		if (pWorkingDirectory == null) {
			pWorkingDirectory = pBase;
		}
	}

	/**
	 * Converts the given map to a "key=value" strings array
	 * 
	 * @param aEnvironmentMap
	 *            Environment map
	 * @return The corresponding array
	 */
	protected String[] convertEnvironmentMapToArray(
			final Map<String, String> aEnvironmentMap) {

		final String[] environment = new String[aEnvironmentMap.size()];

		int i = 0;
		for (Entry<String, String> entry : aEnvironmentMap.entrySet()) {
			environment[i++] = entry.getKey() + "=" + entry.getValue();
		}

		return environment;
	}

	/**
	 * Prepares the command line array
	 * 
	 * @param aDebugMode
	 *            Debug mode flag
	 * @return The command line array
	 * @throws CoreException
	 *             The PSEM2M start script doesn't exist
	 */
	protected String[] makeCommandLine(final boolean aDebugMode)
			throws CoreException {

		// Find the start script
		final File runScript = new File(pHome, "bin/psem2m.sh");
		if (!runScript.exists()) {
			// The script must exist, of course
			throw RunnerPlugin.prepareException(
					"No psem2m.sh script found in PSEM2M_HOME", null);
		}

		final List<String> commandLine = new ArrayList<String>();
		commandLine.add("/bin/bash");
		commandLine.add(runScript.getAbsolutePath());

		if (aDebugMode) {
			commandLine.add("debug");

		} else {
			commandLine.add("start");
		}

		return commandLine.toArray(new String[0]);
	}

	/**
	 * Runs the platform using the PSEM2M_HOME/bin/psem2m.sh script
	 * 
	 * @param aLaunch
	 *            Current launch context
	 * 
	 * @param aDebugMode
	 *            If true, prepend debug options to the script arguments
	 */
	public Process runPlatform(final ILaunch aLaunch, final boolean aDebugMode)
			throws CoreException {

		// Prepare working directory
		if (!pWorkingDirectory.exists()) {
			pWorkingDirectory.mkdirs();
		}

		// Prepare arguments
		final String[] commandLine = makeCommandLine(aDebugMode);

		// Prepare environment
		final Map<String, String> environmentMap = new HashMap<String, String>();
		environmentMap.put("PSEM2M_HOME", pHome.getAbsolutePath());
		environmentMap.put("PSEM2M_BASE", pBase.getAbsolutePath());

		if (aDebugMode) {
			environmentMap.put("PSEM2M_DEBUG_PORT",
					Integer.toString(pBaseDebugPort));
		}

		final String[] environmentArray = convertEnvironmentMapToArray(environmentMap);

		// Run it !
		final Process execProcess = DebugPlugin.exec(commandLine,
				pWorkingDirectory, environmentArray);

		// Add the process to the launch
		DebugPlugin.newProcess(aLaunch, execProcess, commandLine[0]);

		return execProcess;
	}
}
