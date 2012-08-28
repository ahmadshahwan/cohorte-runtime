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
package org.psem2m.isolates.loggers;

import java.util.List;

/**
 * @author isandlatech (www.isandlatech.com) - ogattaz
 * 
 */
public interface ILogChannelsSvc {

    /**
     * @return the list of available channels
     */
    List<ILogChannelSvc> getChannels();

    /**
     * @return the list of the IDs of the available channels
     */
    List<String> getChannelsIds();

    /**
     * @param aChannelId
     *            the channel id of the logger to retrieve
     * @return the instance of Logger corresponding to the channel id
     */
    ILogChannelSvc getLogChannel(String aChannelId) throws Exception;
}
