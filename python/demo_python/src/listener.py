#!/usr/bin/python
#-- Content-encoding: utf-8 --
"""
@author: Thomas Calmant
"""

from psem2m.component.decorators import ComponentFactory, Provides, Requires, \
    Property, Validate, Invalidate
from psem2m.utilities import SynchronizedClassMethod
import threading

@ComponentFactory("SensorListener")
@Requires("http", "HttpService")
@Provides("demo.sensor.listener")
@Property("max_lines", "output.lines", 10)
class SensorListener(object):
    """
    Sensor listener
    """
    def __init__(self):
        """
        Constructor
        """
        self.lines = []
        self.errors = []
        self.max_lines = 100
        self.lock = threading.Lock()


    @Validate
    @SynchronizedClassMethod('lock')
    def validate(self, context):
        """
        Component validated
        """
        self.http.register_servlet("/stat", self)
        del self.lines[:]
        del self.errors[:]


    @Invalidate
    @SynchronizedClassMethod('lock')
    def invalidate(self, context):
        """
        Component invalidated
        """
        self.http.unregister_servlet(self)
        del self.lines[:]
        del self.errors[:]


    @SynchronizedClassMethod('lock')
    def notify(self, sensor_id, message, new_state, old_state):
        """
        Listener implementation
        """
        line = "From %s: %s (%d -> %d)" % (sensor_id, message, old_state,
                                           new_state)
        self.lines.insert(0, line)
        while len(self.lines) > int(self.max_lines):
            self.lines.pop()


    @SynchronizedClassMethod('lock')
    def error(self, sensor_id, message, error_code):
        """
        Listener implementation
        """
        line = "From %s: %s (Code: %d)" % (sensor_id, message, error_code)
        self.errors.insert(0, line)
        while len(self.errors) > int(self.max_lines):
            self.errors.pop()


    def do_GET(self, handler):
        """
        HTTP requests
        """
        with self.lock:
            str_lines = '\n'.join(["\t<li>%s</li>" % line
                                   for line in self.lines])
            str_errors = '\n'.join(["\t<li>%s</li>" % error
                                    for error in self.errors])

        content = """<html>
<head>
<title>Demo Python</title>
</head>
<body>
<h1>Demo Python</h1>
<h2>Lines :</h2>
<ul>
{lines}
</ul>
<h2>Errors :</h2>
<ul>
{errors}
</ul>
</body>
</html>
        """.format(lines=str_lines, errors=str_errors)

        # Send headers
        handler.send_response(200)
        handler.send_header("content-type", "text/html")
        handler.send_header("content-length", len(content))
        handler.end_headers()

        # Send content
        handler.wfile.write(content)
