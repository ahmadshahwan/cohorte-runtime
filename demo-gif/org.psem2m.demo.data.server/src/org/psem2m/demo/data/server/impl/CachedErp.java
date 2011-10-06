/**
 * File:   CachedErp.java
 * Author: Thomas Calmant
 * Date:   6 oct. 2011
 */
package org.psem2m.demo.data.server.impl;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.NoSuchElementException;
import java.util.Set;
import java.util.SortedSet;

import org.psem2m.demo.data.cache.IDataCache;
import org.psem2m.demo.erp.api.beans.CachedItemBean;
import org.psem2m.demo.erp.api.beans.CachedItemStockBean;
import org.psem2m.demo.erp.api.beans.ItemBean;
import org.psem2m.demo.erp.api.services.IErpDataProxy;

/**
 * Behaves like the ERP, but using the cache
 * 
 * @author Thomas Calmant
 */
public class CachedErp {

    /**
     * Uses the cache to act like {@link IErpDataProxy#getItem(String)}
     * 
     * If ID is '?', returns a randomly chosen item. Returns null on error.
     * 
     * @param aCache
     *            The data cache
     * @param aItemId
     *            The ID of item to retrieve
     * @return The selected item from cache, or null
     */
    public CachedItemBean getItem(final IDataCache aCache, final String aItemId) {

        final ItemBean item;
        final String itemId;

        if ("?".equals(aItemId)) {
            item = aCache.getRandomItem();
            if (item != null) {
                itemId = item.getId();
            } else {
                itemId = null;
            }

        } else {
            item = aCache.getItem(aItemId);
            itemId = aItemId;
        }

        final long itemAge = aCache.getItemInformationAge(itemId);

        if (item != null && itemAge != -1) {
            // Return the cached bean
            return new CachedItemBean(item, itemAge);
        }

        return null;
    }

    /**
     * Uses the cache to to act like
     * {@link IErpDataProxy#getItems(String, int, boolean, String)}
     * 
     * @param aCache
     *            The data cache
     * @param aCategory
     *            Category to list
     * @param aItemsCount
     *            Maximum number of items to retrieve (&lt;= 0 for unlimited)
     * @param aRandomize
     *            Retrieve "aItemsCount" randomly from the category
     * @param aBaseId
     *            Retrieve items starting by item at aBaseId + 1
     * 
     * @return All elements of the category, or an empty array.
     */
    public CachedItemBean[] getItems(final IDataCache aCache,
            final String aCategory, final int aItemsCount,
            final boolean aRandomize, final String aBaseId) {

        // Get the items of the category
        final SortedSet<String> categoryItems = aCache
                .getCategoryItems(aCategory);
        if (categoryItems == null) {
            // Empty category
            return new CachedItemBean[0];
        }

        // Selected IDs
        final Set<String> itemsIds = new HashSet<String>();

        if (aRandomize) {
            // Case 1 : random
            itemsIds.addAll(getRandomItems(categoryItems, aItemsCount));

        } else {
            // Case 2 : base Id
            itemsIds.addAll(paginateItems(categoryItems, aBaseId, aItemsCount));
        }

        // Result array
        final CachedItemBean[] resultArray = new CachedItemBean[itemsIds.size()];
        int i = 0;

        for (String itemId : itemsIds) {

            // Get information about the item
            final ItemBean item = aCache.getItem(itemId);
            final long itemAge = aCache.getItemInformationAge(itemId);

            // Store the bean
            resultArray[i++] = new CachedItemBean(item, itemAge);
        }

        return resultArray;
    }

    /**
     * Uses the cache to act like {@link IErpDataProxy#getItemsStock(String[])}
     * 
     * @param aCache
     *            The data cache
     * @param aItemIds
     *            An array of items
     * @return The cached stock values, or an empty array
     */
    public CachedItemStockBean[] getItemsStock(final IDataCache aCache,
            final String[] aItemIds) {

        // Result array
        final CachedItemStockBean[] resultArray = new CachedItemStockBean[aItemIds.length];

        for (int i = 0; i < aItemIds.length; i++) {

            // Get the ID
            final String itemId = aItemIds[i];

            // Read the cache
            final long beanStock = aCache.getItemStock(itemId);
            final long stockAge = aCache.getItemStockInformationAge(itemId);

            if (beanStock != -1 && stockAge != -1) {
                // Cache is valid, prepare a bean
                final CachedItemStockBean stockBean = new CachedItemStockBean(
                        itemId, beanStock, stockAge);
                resultArray[i] = stockBean;
            }
        }

        return resultArray;
    }

    /**
     * Retrieves aItemsCount random items from the given set.
     * 
     * If aItemsCount &lt;= 0, returns the whole list.
     * 
     * @param aItemsIds
     *            A set of item IDs
     * @param aCount
     *            Maximum number of IDs to retrieve
     * @return A random set
     */
    private Collection<String> getRandomItems(final Set<String> aItemsIds,
            final int aCount) {

        // Compute the number of items to retrieve
        final int itemsCount;
        if (aCount <= 0 || aCount > aItemsIds.size()) {
            itemsCount = aItemsIds.size();
        } else {
            itemsCount = aCount;
        }

        // Shuffle the IDs
        final List<String> idsList = new ArrayList<String>(aItemsIds);
        Collections.shuffle(idsList);

        // Return a sub list
        return idsList.subList(0, itemsCount);
    }

    /**
     * Returns a page of items from the given items
     * 
     * @param aItemsIds
     *            IDs to paginate
     * @param aBaseId
     *            Base page ID (excluded) or null
     * @param aItemsCount
     *            Maximum number of items in the page
     * @return The IDs to show in the page
     */
    private Collection<String> paginateItems(final SortedSet<String> aItemsIds,
            final String aBaseId, final int aItemsCount) {

        // Basic test of items count
        if (aItemsCount <= 0 || aItemsCount >= aItemsIds.size()) {
            return aItemsIds;
        }

        // Get a sub-set of the IDs, beginning just after the baseID
        final SortedSet<String> basedSet;
        if (aBaseId == null || aBaseId.isEmpty()) {
            basedSet = aItemsIds;

        } else if (aItemsIds.contains(aBaseId)) {
            // Base id found
            final SortedSet<String> subSet = aItemsIds.tailSet(aBaseId);

            // Get the following ID
            try {
                basedSet = subSet.tailSet(subSet.iterator().next());

            } catch (NoSuchElementException e) {
                // No element after the base ID
                return null;
            }

        } else {
            // Invalid base
            return null;
        }

        // Compute the new items count
        final int itemsCount = Math.min(aItemsCount, basedSet.size());

        // Set up the result collection
        final List<String> resultList = new ArrayList<String>(itemsCount);
        int i = 0;
        for (String itemId : basedSet) {

            if (i == itemsCount) {
                break;
            }

            resultList.add(itemId);
            i++;
        }

        return resultList;
    }
}
