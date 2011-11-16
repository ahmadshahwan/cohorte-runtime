{
    "name":"DataServerApplication",
    "components":[
        {
            "name":"dataServer-Exported",
            "type":"server-exported",
            "isolate":"isolate-1",
            "properties":{
                "endpoint.name":"dataserver",
                
            },
            "wires":{
                "applyCart":"ApplyCart.serverEndpoint",
                "getItem":"GetItem.serverEndpoint",
                "getItems":"GetItems.serverEndpoint",
                "getItemsStock":"GetItemsStock.serverEndpoint"
            }
        },
        {
            "name":"erpProxy",
            "type":"erp-proxy-json-rpc",
            "isolate":"isolate-1",
            "properties":{
                "host":"localhost",
                "port":8080
            }
        }
    ],
    "composets":[
        {
            "name":"GetItem",
            "components":[
                {
                    "name":"serverEndpoint",
                    "type":"server-endpoint-getItem",
                    "isolate":"isolate-1",
                    "wires":{
                        "normalizer":"resultNormalizer",
                        "next":"fallbackOnCache"
                    }
                },
                {
                    "name":"resultNormalizer",
                    "type":"normalizer-getItem",
                    "isolate":"isolate-1"
                },
                {
                    "name":"fallbackOnCache",
                    "type":"fall-back",
                    "isolate":"isolate-1",
                    "wires":{
                        "next":"erpChain.getCacheFirst",
                        "second":"fallback.getCache"
                    }
                }
            ],
            "composets":[
                {
                    "name":"fallback",
                    "components":[
                        {
                            "name":"getCache",
                            "type":"get-cache",
                            "isolate":"isolate-cache",
                            "properties":{
                                "cacheChannel":"cache-getItem",
                                "requestKeyName":"itemId"
                            }
                        }
                    ]
                },
                {
                    "name":"erpChain",
                    "components":[
                        {
                            "name":"getCacheFirst",
                            "type":"get-cache-if-recent",
                            "isolate":"isolate-cache",
                            "properties":{
                                "cacheChannel":"cache-getItem",
                                "requestKeyName":"itemId",
                                "maxCacheAge":1000
                            },
                            "wires":{
                                "next":"storeErpResult"
                            }
                        },
                        {
                            "name":"storeErpResult",
                            "type":"store-cache",
                            "isolate":"isolate-cache",
                            "properties":{
                                "cacheChannel":"cache-getItem",
                                "resultKeyName":"id"
                            },
                            "wires":{
                                "next":"safeErpCaller"
                            }
                        }
                    ]
                },
                {
                    "name":"erpCaller",
                    "components":[
                        {
                            "name":"safeErpCaller",
                            "type":"exception-catcher",
                            "wires":{
                                "next":"erpCaller"
                            }
                        },
                        {
                            "name":"erpCaller",
                            "type":"erp-caller",
                            "properties":{
                                "method":"getItem"
                            },
                            "wires":{
                                "next":"erpProxy"
                            }
                        }
                    ]
                }
            ]
        },
        {
            "name":"GetItems",
            "components":[
                {
                    "name":"serverEndpoint",
                    "type":"server-endpoint-getItems",
                    "wires":{
                        "normalizer":"resultNormalizer",
                        "next":"fallbackOnCache"
                    }
                },
                {
                    "name":"resultNormalizer",
                    "type":"normalizer-getItems"
                },
                {
                    "name":"fallbackOnCache",
                    "type":"fall-back",
                    "wires":{
                        "next":"erpChain.getCacheFirst",
                        "second":"fallback.getCache"
                    }
                }
            ],
            "composets":[
                {
                    "name":"fallback",
                    "components":[
                        {
                            "name":"getCache",
                            "type":"get-cache",
                            "isolate":"isolate-cache",
                            "properties":{
                                "cacheChannel":"cache-getItems",
                                "channelEntryName":"ids"
                            }
                        }
                    ]
                },
                {
                    "name":"erpChain",
                    "components":[
                        {
                            "name":"getCacheFirst",
                            "type":"get-cache-if-recent",
                            "isolate":"isolate-cache",
                            "properties":{
                                "cacheChannel":"cache-getItems",
                                "channelEntryName":"ids",
                                "maxCacheAge":1000
                            },
                            "wires":{
                                "next":"storeErpResult"
                            }
                        },
                        {
                            "name":"storeErpResult",
                            "type":"store-cache",
                            "isolate":"isolate-cache",
                            "properties":{
                                "cacheChannel":"cache-getItems",
                                "channelEntryName":"ids"
                            },
                            "wires":{
                                "next":"safeErpCaller"
                            }
                        }
                    ]
                },
                {
                    "name":"erpCaller",
                    "components":[
                        {
                            "name":"safeErpCaller",
                            "type":"exception-catcher",
                            "wires":{
                                "next":"erpCaller"
                            }
                        },
                        {
                            "name":"erpCaller",
                            "type":"erp-caller",
                            "properties":{
                                "method":"getItems"
                            },
                            "wires":{
                                "next":"erpProxy"
                            }
                        }
                    ]
                }
            ]
        },
        {
            "name":"GetItemsStock",
            "components":[
                {
                    "name":"serverEndpoint",
                    "type":"server-endpoint-getItemsStock",
                    "isolate":"isolate-cache",
                    "wires":{
                        "normalizer":"resultNormalizer",
                        "next":"computeQueuedCarts"
                    }
                },
                {
                    "name":"resultNormalizer",
                    "type":"normalizer-getItemsStock",
                    "isolate":"isolate-cache"
                },
                {
                    "name":"computeQueuedCarts",
                    "type":"compute-queued-carts",
                    "isolate":"isolate-cache",
                    "properties":{
                        "cartCacheChannel":"carts",
                        "cartItemId":"itemId",
                        "cartItemQuantity":"quantity"
                    },
                    "wires":{
                        "next":"fallbackOnCache"
                    }
                },
                {
                    "name":"fallbackOnCache",
                    "type":"fall-back",
                    "isolate":"isolate-cache",
                    "wires":{
                        "next":"erpChain.getCacheFirst",
                        "second":"fallback.getCache"
                    }
                }
            ],
            "composets":[
                {
                    "name":"fallback",
                    "components":[
                        {
                            "name":"getCache",
                            "type":"get-cache",
                            "isolate":"isolate-cache",
                            "properties":{
                                "cacheChannel":"cache-getItemsStock",
                                "requestKeyName":"itemIds"
                            }
                        }
                    ]
                },
                {
                    "name":"erpChain",
                    "components":[
                        {
                            "name":"getCacheFirst",
                            "type":"get-cache-if-recent",
                            "isolate":"isolate-cache",
                            "properties":{
                                "cacheChannel":"cache-getItemsStock",
                                "requestKeyName":"itemIds",
                                "maxCacheAge":1000
                            },
                            "wires":{
                                "next":"storeErpResult"
                            }
                        },
                        {
                            "name":"storeErpResult",
                            "type":"store-cache",
                            "isolate":"isolate-cache",
                            "properties":{
                                "cacheChannel":"cache-getItemsStock",
                            },
                            "wires":{
                                "next":"safeErpCaller"
                            }
                        }
                    ]
                },
                {
                    "name":"erpCaller",
                    "components":[
                        {
                            "name":"safeErpCaller",
                            "type":"exception-catcher",
                            "isolate":"isolate-cache",
                            "wires":{
                                "next":"erpCaller"
                            }
                        },
                        {
                            "name":"erpCaller",
                            "type":"erp-caller",
                            "isolate":"isolate-cache",
                            "properties":{
                                "method":"getItemsStock"
                            },
                            "wires":{
                                "next":"erpProxy"
                            }
                        }
                    ]
                }
            ]
        },
        {
            "name":"ApplyCart",
            "components":[
                {
                    "name":"serverEndpoint",
                    "type":"server-endpoint-applyCart",
                    "wires":{
                        "normalizer":"resultNormalizer",
                        "next":"storeInQueue"
                    }
                },
                {
                    "name":"resultNormalizer",
                    "type":"normalizer-applyCart"
                },
                {
                    "name":"storeInQueue",
                    "type":"store-cache-queue",
                    "isolate":"isolate-cache",
                    "properties":{
                        "cacheChannel":"carts"
                    }
                }
            ]
        },
        {
            "name":"CartsApplier",
            "components":[
                {
                    "name":"scheduler",
                    "type":"cache-queue-poller",
                    "isolate":"isolate-cache",
                    "properties":{
                        "cacheChannel":"carts"
                    },
                    "wires":{
                        "next":"safeErpCaller"
                    }
                },
                {
                    "name":"safeErpCaller",
                    "type":"exception-catcher",
                    "wires":{
                        "next":"erpCaller"
                    }
                },
                {
                    "name":"erpCaller",
                    "type":"erp-caller",
                    "properties":{
                        "method":"applyCart"
                    },
                    "wires":{
                        "next":"erpProxy"
                    }
                }
            ]
        }
    ]
}