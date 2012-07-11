{
    "name":"demo.july2012",
    "components":[
        {
            "name":"temper-1",
            "type":"demo-temperature-fake-factory",
            "isolate":"demo.temper",
            "properties":{
                "temper.value.min":-5,
                "temper.value.max":45
            }
        },
        {
            "name":"temper-2",
            "type":"demo-temperature-fake-factory",
            "isolate":"demo.temper-2"
        },
        {
            "name":"aggregator",
            "type":"demo-sensor-aggregator-factory",
            "isolate":"demo.stratus.aggregator",
            "properties":{
                "poll.delta":1
            }
        },
        {
            "name":"aggregator-UI",
            "type":"demo-sensor-aggregator-ui-factory",
            "isolate":"demo.stratus.aggregator",
            "properties":{
                "servlet.path":"/sensors"
            },
            "wires":{
                "_aggregator":"aggregator"
            }
        }
    ]
}