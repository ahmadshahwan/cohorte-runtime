/*******************************************************************************
 * Copyright (c) 2011 www.isandlatech.com (www.isandlatech.com)
 * All rights reserved. This program and the accompanying materials
 * are made available under the terms of the Eclipse License v1.0
 * which accompanies this distribution, and is available at
 * http://www.eclipse.org/legal/epl-v10.html
 *
 * Contributors:
 *    ogattaz (isandlaTech) - initial API and implementation
 *******************************************************************************/
package org.psem2m.isolates.services.dirs;

import java.io.File;
import java.util.List;

import org.psem2m.isolates.constants.IPlatformProperties;

/**
 * @author isandlatech (www.isandlatech.com) - ogattaz
 * 
 */
public interface IPlatformDirsSvc extends IPlatformProperties {

    /**
     * Retrieves the ProcessBuilder command to run the forker start script,
     * generated by the platform start script
     * 
     * @return The forker start command
     */
    List<String> getForkerStartCommand();

    /**
     * @return the id of the current isolate
     */
    String getIsolateId();

    /**
     * @return the log directory of the current isolate
     * @throws Exception
     */
    File getIsolateLogDir() throws Exception;

    /**
     * @param aIsolateId
     *            the id of an isolate
     * @return the log directory of the isolate
     * @throws Exception
     *             if the hierarchy doesn't exist and can't be created
     */
    File getIsolateLogDir(final String aIsolateId) throws Exception;

    /**
     * @param aIsolateId
     *            the id of an isolate
     * @return The isolate working directory
     */
    File getIsolateWorkingDir(String aIsolateId);

    /**
     * Retrieves the Java executable file
     * 
     * @return The Java executable file
     */
    File getJavaExecutable();

    /**
     * Retrieves the PSEM2M_BASE value
     * 
     * <pre>
     * -Dorg.psem2m.platform.base=${workspace_loc}/psem2m/platforms/felix.user.dir
     * </pre>
     * 
     * @return the base directory of the platform
     */
    File getPlatformBaseDir();

    /**
     * Retrieves the PSEM2M_HOME value
     * 
     * <pre>
     * -Dorg.psem2m.platform.home=/usr/share/psem2m
     * </pre>
     * 
     * @return
     */
    File getPlatformHomeDir();

    /**
     * @return the log directory of the platform
     * @throws Exception
     */
    File getPlatformLogDir() throws Exception;

    /**
     * Retrieves the platform root directories : home, base and working
     * directory
     * 
     * @return The platform root directories
     */
    File[] getPlatformRootDirs();

    /**
     * Retrieves all known repositories, in order of priority.
     * 
     * The first element is the base repository, then the home repository, then
     * the system repository.
     * 
     * @return An array with at least one element
     */
    File[] getRepositories();
}