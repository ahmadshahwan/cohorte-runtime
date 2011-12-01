/**
 * File:   ErpCaller.java
 * Author: Thomas Calmant
 * Date:   14 nov. 2011
 */
package org.psem2m.composer.demo.cache;

import java.io.Serializable;
import java.util.Collection;
import java.util.HashMap;
import java.util.Map;

import org.apache.felix.ipojo.annotations.Component;
import org.apache.felix.ipojo.annotations.Invalidate;
import org.apache.felix.ipojo.annotations.Property;
import org.apache.felix.ipojo.annotations.Provides;
import org.apache.felix.ipojo.annotations.Requires;
import org.apache.felix.ipojo.annotations.Validate;
import org.osgi.framework.BundleException;
import org.psem2m.composer.demo.CComponentPojo;
import org.psem2m.composer.demo.CComponentsConstants;
import org.psem2m.composer.demo.IComponent;
import org.psem2m.composer.demo.IComponentContext;
import org.psem2m.demo.data.cache.ICacheDequeueChannel;
import org.psem2m.demo.data.cache.ICacheFactory;
import org.psem2m.isolates.base.IIsolateLoggerSvc;
import org.psem2m.isolates.base.Utilities;

/**
 * getItem treatment chain entry point
 * 
 * @author Thomas Calmant
 */
@Component(name = CComponentsConstants.COMPONENT_STORE_IN_CACHE_QUEUE)
@Provides(specifications = IComponent.class)
public class StoreInCacheQueue extends CComponentPojo implements IComponent {

    /** The cache factory */
    @Requires
    private ICacheFactory pCache;

    /** The name of the channel to poll */
    @Property(name = "cacheChannel")
    private String pCacheChannelName;

    /** The cart ID key */
    @Property(name = "cartIdKey", value = "id")
    private String pCartIdKey;

    /** The cart lines key */
    @Property(name = "cartLinesKey", value = "lines")
    private String pCartLinesKey;

    /** The logger */
    @Requires
    private IIsolateLoggerSvc pLogger;

    /** The instance name */
    @Property(name = CComponentsConstants.PROPERTY_INSTANCE_NAME)
    private String pName;

    /*
     * (non-Javadoc)
     * 
     * @see
     * org.psem2m.composer.test.api.IComponent#computeResult(org.psem2m.composer
     * .test.api.IComponentContext)
     */
    @Override
    public IComponentContext computeResult(final IComponentContext aContext)
            throws Exception {

        final Map<String, Object> cartMap = aContext.getRequest();

        /* Test cart ID */
        if (cartMap == null) {
            aContext.addError(pName, "Null cart");
            // log the error
            logContextError(pLogger, aContext);
            return aContext;
        }

        if (!cartMap.containsKey(pCartIdKey)) {
            aContext.addError(pName, "Cart doesn't have an ID");
            // log the error
            logContextError(pLogger, aContext);
            return aContext;
        }

        /* Test cart lines */
        final Object cartLinesObject = Utilities.arrayToIterable(cartMap
                .get(pCartLinesKey));

        if (!(cartLinesObject instanceof Collection)
                || ((Collection<?>) cartLinesObject).isEmpty()) {

            aContext.addError(pName, "Empty cart or invalid lines");
            // log the error
            logContextError(pLogger, aContext);
            return aContext;
        }

        /* Store the current context in the cache */
        final ICacheDequeueChannel<?, Serializable> channel = pCache
                .openDequeueChannel(pCacheChannelName);

        channel.add(aContext);

        // TODO: wait until we get a response
        final Map<String, Object> resultMap = new HashMap<String, Object>();
        resultMap.put(KEY_RESULT, "Cart in queue...");
        aContext.setResult(resultMap);

        return aContext;
    }

    /*
     * (non-Javadoc)
     * 
     * @see org.psem2m.composer.demo.impl.CComposable#getName()
     */
    @Override
    public String getName() {

        return pName;
    }

    /*
     * (non-Javadoc)
     * 
     * @see org.psem2m.isolates.base.activators.CPojoBase#invalidatePojo()
     */
    @Override
    @Invalidate
    public void invalidatePojo() throws BundleException {

        pLogger.logInfo(this, "invalidatePojo", "cpnt=[%25s] Gone",
                getShortName());
    }

    /*
     * (non-Javadoc)
     * 
     * @see org.psem2m.isolates.base.activators.CPojoBase#validatePojo()
     */
    @Override
    @Validate
    public void validatePojo() throws BundleException {

        pLogger.logInfo(this, "validatePojo", "cpnt=[%25s] Ready",
                getShortName());
    }
}
