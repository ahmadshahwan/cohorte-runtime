/**
 * File:   ErpCaller.java
 * Author: Thomas Calmant
 * Date:   14 nov. 2011
 */
package org.psem2m.composer.demo.impl.getItemsStock;

import java.io.Serializable;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.BlockingDeque;
import java.util.concurrent.LinkedBlockingDeque;

import org.apache.felix.ipojo.annotations.Component;
import org.apache.felix.ipojo.annotations.Property;
import org.apache.felix.ipojo.annotations.Provides;
import org.apache.felix.ipojo.annotations.Requires;
import org.osgi.framework.BundleException;
import org.psem2m.composer.demo.DemoComponentsConstants;
import org.psem2m.composer.test.api.IComponent;
import org.psem2m.demo.data.cache.ICacheDequeueChannel;
import org.psem2m.demo.data.cache.ICacheFactory;
import org.psem2m.demo.data.cache.ICachedObject;
import org.psem2m.isolates.base.IIsolateLoggerSvc;
import org.psem2m.isolates.base.activators.CPojoBase;

/**
 * getItem treatment chain entry point
 * 
 * @author Thomas Calmant
 */
@Component(name = DemoComponentsConstants.COMPONENT_COMPUTE_QUEUED_CARTS)
@Provides(specifications = IComponent.class)
public class ComputeQueuedCarts extends CPojoBase implements IComponent {

    /** The cache factory */
    @Requires
    private ICacheFactory pCache;

    /** The cart channel name */
    @Property(name = "cartCacheChannel")
    private String pCartChannelName;

    /** The item ID key in a cart line */
    @Property(name = "cartItemId")
    private String pCartItemIdKey;

    /** The item quantity key in a cart line */
    @Property(name = "cartItemQuantity")
    private String pCartItemQuantitydKey;

    /** The instance name */
    @Property(name = DemoComponentsConstants.PROPERTY_INSTANCE_NAME)
    private String pInstanceName;

    /** The logger */
    @Requires
    private IIsolateLoggerSvc pLogger;

    /** The next component of the chain */
    @Requires(id = DemoComponentsConstants.WIRE_NEXT)
    private IComponent pNext;

    /*
     * (non-Javadoc)
     * 
     * @see org.psem2m.composer.test.api.IComponent#computeResult(java.util.Map)
     */
    @Override
    public Map<String, Object> computeResult(final Map<String, Object> aData)
            throws Exception {

        // Call the chain...
        final Map<String, Object> computedMap = pNext.computeResult(aData);

        // Open the channel
        final ICacheDequeueChannel<Serializable, Serializable> channel = pCache
                .openDequeueChannel(pCartChannelName);

        // Get a copy of the queue
        final BlockingDeque<ICachedObject<Serializable>> queueCopy = new LinkedBlockingDeque<ICachedObject<Serializable>>(
                channel);

        // Reserved quantities map
        final Map<String, Integer> reservedQuantities = new HashMap<String, Integer>();

        // Get reserved quantities
        for (final ICachedObject<Serializable> cachedObject : queueCopy) {

            @SuppressWarnings("unchecked")
            final Map<String, Object> treatedMap = (Map<String, Object>) cachedObject
                    .getObject();

            @SuppressWarnings("unchecked")
            final Map<String, Map<String, Object>> cartRequest = (Map<String, Map<String, Object>>) treatedMap
                    .get(IComponent.KEY_REQUEST);

            for (final String lineId : cartRequest.keySet()) {

                final Map<String, Object> cartLine = cartRequest.get(lineId);

                final String itemId = (String) cartLine.get(pCartItemIdKey);
                final Integer itemQuantity = (Integer) cartLine
                        .get(pCartItemQuantitydKey);

                reservedQuantities.put(itemId, itemQuantity);
            }
        }

        // Remove reserved quantities from the returned stock
        @SuppressWarnings("unchecked")
        final Map<String, Map<String, Object>> resultMap = (Map<String, Map<String, Object>>) computedMap
                .get(IComponent.KEY_RESULT);

        for (final String itemId : resultMap.keySet()) {

            // Get the associated map (stock, quality, ...)
            final Map<String, Object> itemData = resultMap.get(itemId);
            final Integer currentStock = (Integer) itemData.get("stock");

            if (currentStock == null) {
                // Invalid stock
                continue;
            }

            // Find the item ID in the cache
            final Integer reservedQuantity = reservedQuantities.get(itemId);
            if (reservedQuantity != null) {
                // Valid value, reduce the current item stock
                int newStock = currentStock.intValue()
                        - reservedQuantity.intValue();
                if (newStock < 0) {
                    // Something went wrong ?
                    newStock = 0;
                }

                itemData.put("stock", newStock);
            }
        }

        computedMap.put(IComponent.KEY_RESULT, resultMap);
        return computedMap;
    }

    /*
     * (non-Javadoc)
     * 
     * @see org.psem2m.isolates.base.activators.CPojoBase#invalidatePojo()
     */
    @Override
    public void invalidatePojo() throws BundleException {

        pLogger.logInfo(this, "invalidatePojo", "Component", pInstanceName,
                "Gone");
    }

    /*
     * (non-Javadoc)
     * 
     * @see org.psem2m.isolates.base.activators.CPojoBase#validatePojo()
     */
    @Override
    public void validatePojo() throws BundleException {

        pLogger.logInfo(this, "validatePojo", "Component", pInstanceName,
                "Ready");
    }
}
