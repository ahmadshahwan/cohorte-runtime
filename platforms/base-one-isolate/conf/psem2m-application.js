{
    "appId":"dev-app-one-isolate",
    "isolates":[
        {
            "id":"isolate-one",
            "kind":"felix",
            "vmArgs":[
                      "-Xms512m","-Xmx512m" 
            ],
            "bundles":[
               {
                   "symbolicName":"org.psem2m.isolates.demo.services.ui.viewer",
                   "optional":false,
                   "properties":{
                   	"psem2m.demo.ui.viewer.top":"0scr",
                   	"psem2m.demo.ui.viewer.left":"0.25scr",
                   	"psem2m.demo.ui.viewer.width":"0.25scr",
                   	"psem2m.demo.ui.viewer.height":"0.5scr",
                   	"psem2m.demo.ui.viewer.color":"Moccasin"
                   }
               },
                {
                    "symbolicName":"org.apache.felix.shell.remote",
                    "properties":{
                    	"osgi.shell.telnet.port":"6000"
                    }
                },
                {
                    "symbolicName":"org.apache.felix.shell.tui"
                },
                {
                    "symbolicName":"org.psem2m.isolates.forker"
                },

                {
                    "symbolicName":"org.psem2m.isolates.tracer"
                }
            ]
        }
    ]
}