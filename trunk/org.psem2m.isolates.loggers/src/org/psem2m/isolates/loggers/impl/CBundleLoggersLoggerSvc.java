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
package org.psem2m.isolates.loggers.impl;

import org.psem2m.isolates.base.CBundleLoggerBase;
import org.psem2m.isolates.loggers.CBundleLoggersActivator;
import org.psem2m.isolates.loggers.IBundleLoggersLoggerSvc;

/**
 * @author isandlatech (www.isandlatech.com) - ogattaz
 * 
 */
public class CBundleLoggersLoggerSvc extends CBundleLoggerBase implements
		IBundleLoggersLoggerSvc {

	/**
	 * Explicit default constructor
	 */
	public CBundleLoggersLoggerSvc() {
		super();
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see org.psem2m.isolates.base.CPojoBase#invalidatePojo()
	 */
	@Override
	public void invalidatePojo() {
		// logs in the bundle output
		logInfo(this, "invalidatePojo", "INVALIDATE", toDescription());

		setActivityLoggerBase(null);
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see org.psem2m.isolates.base.CPojoBase#validatePojo()
	 */
	@Override
	public void validatePojo() {
		setActivityLoggerBase(CBundleLoggersActivator.getInstance());

		// logs in the bundle output
		logInfo(this, "validatePojo", "VALIDATE", toDescription());
	}

}
