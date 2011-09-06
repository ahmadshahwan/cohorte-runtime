/**
 * File:   IIsolateDescr.java
 * Author: Thomas Calmant
 * Date:   2 sept. 2011
 */
package org.psem2m.isolates.config.json;

import java.io.Serializable;
import java.util.List;
import java.util.Set;

/**
 * Describes an isolate configuration
 * 
 * @author Thomas Calmant
 */
public interface IIsolateDescr extends Serializable {

    /**
     * Retrieves the list of bundles to be installed in the isolate. Can't be
     * null and should'nt be empty.
     * 
     * @return The list of bundles of the isolate
     */
    Set<IBundleDescr> getBundles();

    /**
     * Retrieves the isolate ID. Can't be null nor empty.
     * 
     * @return the isolate ID
     */
    String getId();

    /**
     * Retrieves the list of Java Virtual Machine arguments to be used when
     * starting the isolate process. Can be null.
     * 
     * @return The isolate JVM arguments
     */
    List<String> getVMArgs();
}
