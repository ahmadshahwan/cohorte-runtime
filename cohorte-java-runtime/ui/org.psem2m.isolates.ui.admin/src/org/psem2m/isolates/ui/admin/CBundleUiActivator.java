/*******************************************************************************
 * Copyright (c) 2011 www.isandlatech.com (www.isandlatech.com)
 * All rights reserved. This program and the accompanying materials
 * are made available under the terms of the Eclipse Public License v1.0
 * which accompanies this distribution, and is available at
 * http://www.eclipse.org/legal/epl-v10.html
 *
 * Contributors:
 *    ogattaz (isandlaTech) - initial API and implementation
 *******************************************************************************/
package org.psem2m.isolates.ui.admin;

import org.osgi.framework.BundleContext;
import org.psem2m.isolates.base.activators.CActivatorBase;
import org.psem2m.isolates.base.activators.IActivatorBase;

/**
 * @author ogattaz
 * 
 */
public class CBundleUiActivator extends CActivatorBase implements
        IActivatorBase {

    /** Current instance **/
    private static CBundleUiActivator sSingleton = null;

    /**
     * Retrieves the current bundle instance
     * 
     * @return The bundle instance
     */
    public static CBundleUiActivator getInstance() {

        return sSingleton;
    }

    /*
     * (non-Javadoc)
     * 
     * @see
     * org.osgi.framework.BundleActivator#start(org.osgi.framework.BundleContext
     * )
     */
    @Override
    public void start(final BundleContext bundleContext) throws Exception {

        // Store the singleton reference
        sSingleton = this;

        super.start(bundleContext);
    }

    /*
     * (non-Javadoc)
     * 
     * @see
     * org.osgi.framework.BundleActivator#stop(org.osgi.framework.BundleContext)
     */
    @Override
    public void stop(final BundleContext bundleContext) throws Exception {

        super.stop(bundleContext);

        // Forget the singleton reference
        sSingleton = null;
    }
}