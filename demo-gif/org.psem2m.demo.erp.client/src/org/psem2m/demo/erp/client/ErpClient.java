/**
 * File:   ErpClient.java
 * Author: Thomas Calmant
 * Date:   4 oct. 2011
 */
package org.psem2m.demo.erp.client;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.StringWriter;
import java.net.HttpURLConnection;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Scanner;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerConfigurationException;
import javax.xml.transform.TransformerException;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;

import org.apache.felix.ipojo.annotations.Component;
import org.apache.felix.ipojo.annotations.Provides;
import org.apache.felix.ipojo.annotations.Requires;
import org.apache.felix.ipojo.annotations.Validate;
import org.osgi.framework.BundleException;
import org.psem2m.demo.erp.api.beans.ItemBean;
import org.psem2m.demo.erp.api.services.IErpDataProxy;
import org.psem2m.isolates.base.IIsolateLoggerSvc;
import org.psem2m.isolates.base.activators.CPojoBase;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.w3c.dom.Text;
import org.xml.sax.SAXException;

/**
 * Implementation of the ERP proxy. Sends requests to the home-brewed Python ERP
 * 
 * @author Thomas Calmant
 */
@Component(name = "demo-erp-client-python-factory", publicFactory = false, propagation = true)
@Provides(specifications = IErpDataProxy.class)
public class ErpClient extends CPojoBase implements IErpDataProxy {

    /** getItemsStock() method URI */
    public static final String GET_ITEMS_STOCK_URI = "/getItemsStock";

    /** getItems() method URI */
    public static final String GET_ITEMS_URI = "/getItems";

    /** ERP Client configuration */
    private ErpClientConfig pConfig;

    /** Log service */
    @Requires
    private IIsolateLoggerSvc pLogger;

    /**
     * Default constructor
     */
    public ErpClient() {

        super();
    }

    /**
     * Converts the given DOM document to an XML string
     * 
     * @param aDocument
     *            DOM Document to be converted
     * @return The XML string or null
     */
    protected String domToString(final Document aDocument) {

        if (aDocument == null) {
            return null;
        }

        // Prepare the transformer
        final Transformer transformer;
        try {
            final TransformerFactory transfromerFactory = TransformerFactory
                    .newInstance();

            transformer = transfromerFactory.newTransformer();

        } catch (TransformerConfigurationException e) {
            pLogger.logSevere(this, "domToString",
                    "Error creating the transformer", e);
            return null;
        }

        // Prepare the source
        final DOMSource xmlSource = new DOMSource(aDocument);

        // Prepare the String output
        final StringWriter stringWriter = new StringWriter();
        final StreamResult xmlResult = new StreamResult(stringWriter);

        try {
            // Transform
            transformer.transform(xmlSource, xmlResult);

        } catch (TransformerException e) {
            pLogger.logSevere(this, "domToString",
                    "Error transforming the Document into a String", e);
            return null;
        }

        // Retrieve the result string
        return stringWriter.toString();
    }

    /**
     * Prepares an access URL for the given URI in the ERP
     * 
     * @param aUri
     *            URI in the ERP ("/" if null)
     * @param aQuery
     *            Request parameters (can be null)
     * @return The forged URL
     * @throws MalformedURLException
     *             The generated URL is invalid
     */
    protected URL forgeUrl(final String aUri, final String aQuery)
            throws MalformedURLException {

        // Get the access port
        final int port = pConfig.getErpPort();

        // Prepare the URL
        final StringBuilder urlBuilder = new StringBuilder("http://localhost:");
        urlBuilder.append(port);

        // Append the URI
        if (aUri == null || !aUri.startsWith("/")) {
            urlBuilder.append("/");
        }

        if (aUri != null) {
            urlBuilder.append(aUri);
        }

        // Append the query, if any
        if (aQuery != null && !aQuery.isEmpty()) {

            if (!aQuery.startsWith("?")) {
                urlBuilder.append("?");
            }

            urlBuilder.append(aQuery);
        }

        return new URL(urlBuilder.toString());
    }

    /**
     * Retrieves the DOM document builder
     * 
     * @return A the DOM document builder, null on error
     */
    protected DocumentBuilder getDomDocumentBuilder() {

        // Prepare the DOM document creation
        try {
            final DocumentBuilderFactory docFactory = DocumentBuilderFactory
                    .newInstance();
            return docFactory.newDocumentBuilder();

        } catch (ParserConfigurationException e) {
            pLogger.logSevere(this, "getDomDocumentBuilder",
                    "Can't create a document builder.");
        }

        return null;
    }

    /**
     * Retrieves the content of the first child of given element with the given
     * tag name.
     * 
     * @param aElement
     *            A parent element
     * @param aTagName
     *            A child tag name
     * @return The child node value, null on error
     */
    protected String getElementChildValue(final Element aElement,
            final String aTagName) {

        if (aElement == null || aTagName == null) {
            return null;
        }

        final Node tagNode = aElement.getElementsByTagName(aTagName).item(0);
        if (tagNode == null) {
            return null;
        }

        return tagNode.getTextContent();
    }

    /*
     * (non-Javadoc)
     * 
     * @see
     * org.psem2m.demo.erp.api.services.IErpDataProxy#getItems(java.lang.String)
     */
    @Override
    public ItemBean[] getItems(final String aCategory) {

        final String query;
        if (aCategory == null || aCategory.isEmpty()) {
            // No category given
            query = null;

        } else {
            // Prepare the query
            query = "?category=" + aCategory;
        }

        try {
            // Prepare the URL
            final URL erpUrl = forgeUrl(GET_ITEMS_URI, query);

            final String result = getUrlResult(erpUrl);
            if (result != null) {
                return xmlToItemBeans(result);

            } else {
                return null;
            }

        } catch (MalformedURLException e) {
            pLogger.logSevere(this, "getItems", "Error generating the ERP URL",
                    e);
        }

        return null;
    }

    /*
     * (non-Javadoc)
     * 
     * @see
     * org.psem2m.demo.erp.api.services.IErpDataProxy#getItemsStock(java.lang
     * .String[])
     */
    @Override
    public int[] getItemsStock(final String[] aItemIds) {

        if (aItemIds == null) {
            return null;
        }

        try {
            // Prepare the URL
            final URL erpUrl = forgeUrl(GET_ITEMS_URI, null);

            final String result = getUrlPOSTResult(erpUrl,
                    itemsIdsToXml(aItemIds));

            if (result != null) {

                // Analyze the XML result
                final Map<String, Integer> resultMap = xmlToItemStocks(result);
                if (resultMap == null) {
                    return null;
                }

                // Convert the map into an integer array
                final int[] resultArray = new int[aItemIds.length];
                for (int i = 0; i < aItemIds.length; i++) {
                    final Integer stock = resultMap.get(aItemIds[i]);
                    if (stock == null) {
                        resultArray[i] = -1;
                    } else {
                        resultArray[i] = stock.intValue();
                    }
                }

                // Return here
                return resultArray;

            } else {
                return null;
            }

        } catch (MalformedURLException e) {
            pLogger.logSevere(this, "getItems", "Error generating the ERP URL",
                    e);
        }

        return null;
    }

    /**
     * Connects to the given URL and retrieves the POST response content on
     * success. Returns null on error or if the server response code is not 200.
     * 
     * @param aUrl
     *            URL to connect to
     * @return The server response on success, else null
     */
    protected String getUrlPOSTResult(final URL aUrl, final String aPostBody) {

        HttpURLConnection connection = null;
        try {
            // Connect to the URL
            connection = (HttpURLConnection) aUrl.openConnection();

            // Prepare the POST request
            connection.setRequestMethod("POST");
            connection.setDoOutput(true);

            final byte[] bodyContent = aPostBody.getBytes();
            connection.setRequestProperty("content-length",
                    Integer.toString(bodyContent.length));

            connection.getOutputStream().write(bodyContent);

            final int code = connection.getResponseCode();
            if (code != HttpURLConnection.HTTP_ACCEPTED) {
                // Something happened
                return null;
            }

            return (String) connection.getContent();

        } catch (MalformedURLException e) {
            pLogger.logSevere(this, "getItems", "Error generating the ERP URL",
                    e);

        } catch (IOException e) {
            pLogger.logSevere(this, "getItems", "Error connecting the ERP", e);

        } finally {
            // Be nice, disconnect
            if (connection != null) {
                connection.disconnect();
            }
        }

        return null;
    }

    /**
     * Connects to the given URL and retrieves the response content on success.
     * Returns null on error or if the server response code is not 200.
     * 
     * @param aUrl
     *            URL to connect to
     * @return The server response on success, else null
     */
    protected String getUrlResult(final URL aUrl) {

        if (aUrl == null) {
            return null;
        }

        HttpURLConnection connection = null;
        try {
            // Connect to the URL
            connection = (HttpURLConnection) aUrl.openConnection();

            final int code = connection.getResponseCode();
            if (code != HttpURLConnection.HTTP_OK) {
                // Something happened
                return null;
            }

            /*
             * Read the response content See here for more information :
             * http://weblogs
             * .java.net/blog/pat/archive/2004/10/stupid_scanner_1.html
             */
            return new Scanner(connection.getInputStream()).useDelimiter("\\A")
                    .next();

        } catch (MalformedURLException e) {
            pLogger.logSevere(this, "getItems", "Error generating the ERP URL",
                    e);

        } catch (IOException e) {
            pLogger.logSevere(this, "getItems", "Error connecting the ERP", e);

        } finally {
            // Be nice, disconnect
            if (connection != null) {
                connection.disconnect();
            }
        }

        return null;
    }

    /*
     * (non-Javadoc)
     * 
     * @see org.psem2m.isolates.base.activators.CPojoBase#invalidatePojo()
     */
    @Override
    public void invalidatePojo() throws BundleException {

        pLogger.logInfo(this, "invalidatePojo", "Python ERP Client Gone");
    }

    /**
     * Converts the given item IDs array to an XML string
     * 
     * @param aItemIds
     *            An array of item IDs
     * @return The corresponding XML string
     */
    protected String itemsIdsToXml(final String[] aItemIds) {

        if (aItemIds == null) {
            // Invalid array
            return null;
        }

        // Get the document builder
        final DocumentBuilder docBuilder = getDomDocumentBuilder();
        if (docBuilder == null) {
            return null;
        }

        // Write the document
        final Document document = docBuilder.newDocument();

        // The root
        final Element rootNode = document.createElement("items");
        document.appendChild(rootNode);

        for (String itemId : aItemIds) {
            // The nodes
            final Element itemNode = document.createElement("item");
            rootNode.appendChild(itemNode);

            final Element itemIdNode = document.createElement("id");
            itemNode.appendChild(itemIdNode);

            final Text itemIdData = document.createTextNode(itemId);
            itemIdNode.appendChild(itemIdData);
        }

        return domToString(document);
    }

    protected Document parseXmlString(final String aXmlData) {

        // Get the DOM document builder
        final DocumentBuilder docBuilder = getDomDocumentBuilder();
        if (docBuilder == null) {
            return null;
        }

        // Parse the Data
        try {
            return docBuilder.parse(new ByteArrayInputStream(aXmlData
                    .getBytes()));

        } catch (SAXException e) {
            pLogger.logSevere(this, "parseXmlString",
                    "Error parsing the XML data", e);

        } catch (IOException e) {
            pLogger.logSevere(this, "parseXmlString",
                    "Error reading the XML data", e);
        }

        return null;
    }

    /*
     * (non-Javadoc)
     * 
     * @see org.psem2m.isolates.base.activators.CPojoBase#validatePojo()
     */
    @Override
    @Validate
    public void validatePojo() throws BundleException {

        pConfig = new ErpClientConfig();
        try {
            pConfig.init();

        } catch (Exception e) {
            pLogger.logSevere(this, "validatePojo",
                    "Error reading ERP Client configuration.", e);

            throw new BundleException("Error reading ERP Client configuration",
                    e);
        }

        pLogger.logInfo(this, "validatePojo", "Python ERP Client Ready");
    }

    /**
     * Converts the given XML data to an item beans array
     * 
     * @param aXmlData
     *            XML data received from the ERP
     * @return An array of item beans
     */
    protected ItemBean[] xmlToItemBeans(final String aXmlData) {

        // Parse the document
        final Document document = parseXmlString(aXmlData);
        if (document == null) {
            return null;
        }

        // Prepare the result list
        final List<ItemBean> resultList = new ArrayList<ItemBean>();

        // Get the root node
        final Element rootNode = document.getDocumentElement();

        // Grab all items
        final NodeList itemsList = rootNode.getElementsByTagName("item");
        for (int i = 0; i < itemsList.getLength(); i++) {

            final Element itemElement = (Element) itemsList.item(i);

            final String itemId = getElementChildValue(itemElement, "id");
            final String itemName = getElementChildValue(itemElement, "lib");
            final String itemDesc = getElementChildValue(itemElement, "text");
            final String itemPrice = getElementChildValue(itemElement, "price");

            if (itemId != null && itemName != null && itemDesc != null
                    && itemPrice != null) {

                // Construct the bean
                final ItemBean itemBean = new ItemBean();
                itemBean.setId(itemId);
                itemBean.setName(itemName);
                itemBean.setDescription(itemDesc);
                itemBean.setPrice(itemPrice);

                resultList.add(itemBean);
            }
        }

        return resultList.toArray(new ItemBean[resultList.size()]);
    }

    /**
     * Converts the stock nodes in the given XML data to an map
     * 
     * @param aXmlData
     *            XML data received from the ERP
     * @return A itemId - stock map
     */
    protected Map<String, Integer> xmlToItemStocks(final String aXmlData) {

        // Parse the document
        final Document document = parseXmlString(aXmlData);
        if (document == null) {
            return null;
        }

        // Result preparation
        final Map<String, Integer> resultMap = new HashMap<String, Integer>();

        // Get the root node
        final Element rootNode = document.getDocumentElement();

        // Grab all items
        final NodeList itemsList = rootNode.getElementsByTagName("item");
        for (int i = 0; i < itemsList.getLength(); i++) {

            try {
                final Element itemElement = (Element) itemsList.item(i);

                final String itemId = getElementChildValue(itemElement, "id");
                final String itemStock = getElementChildValue(itemElement,
                        "stock");

                if (itemId != null && itemStock != null) {
                    resultMap.put(itemId, Integer.valueOf(itemStock));
                }

            } catch (Exception e) {
                // Ignore exception...
                pLogger.logWarn(this, "xmlToItemsStock",
                        "Error reading a node value : ", e);
            }
        }

        return resultMap;
    }
}