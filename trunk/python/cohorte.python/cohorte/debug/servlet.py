#!/usr/bin/env python
# -- Content-Encoding: UTF-8 --
"""
COHORTE Python bootstrap

**WARNING:**
This module uses the ``argparse`` module if it executed directly to read its
arguments. Argparse is part of the Python standard library since 2.7 and 3.2,
but can be installed manually for previous versions, using
``easy_install -U argparse``.

:author: Thomas Calmant
:license: GPLv3
"""
import cohorte

# Documentation strings format
__docformat__ = "restructuredtext en"

# Boot module version
__version__ = "1.0.0"

# ------------------------------------------------------------------------------

# Pelix framework
from pelix.ipopo.decorators import ComponentFactory, Provides, \
    Validate, Invalidate, Property
import pelix.framework
import pelix.http

# Python standard library
import logging
import sys
import threading
import traceback

# ------------------------------------------------------------------------------

DEFAULT_DEBUG_PATH = '/debug'
""" Default servlet path """

_logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------

CSS_STYLE = """
body {
    font-family: sans;
}

h1 {
    text-align: center;
}

h2 {
    margin-top: 2em;
}

dt {
    font-style: italic;
}

dd {
    margin-bottom: 1em;
}

table {
    font-size: 80%;
}

table tr th {
    background: #DDD;
}

table tr td {
    vertical-align: top;
}

table tr:nth-child(odd) td {
    background: #EFF;
}

table tr:nth-child(even) td {
    background: #CFF;
}

table tr td pre {
    font-family: courier;
    font-size: 100%;
}
"""

# ------------------------------------------------------------------------------

@ComponentFactory('cohorte-debug-servlet-factory')
@Provides(pelix.http.HTTP_SERVLET)
@Property('_path', pelix.http.HTTP_SERVLET_PATH, DEFAULT_DEBUG_PATH)
class DebugServlet(object):
    """
    COHORTE HTTP Signals receiver servlet
    """
    def __init__(self):
        """
        Constructor
        """
        # Servlet path
        self._path = DEFAULT_DEBUG_PATH

        # Bundle context
        self._context = None


    def make_all(self, request):
        """
        Aggregates all content makers
        
        :param request: The HTTP request
        :return: The aggregation of the result of all other make_* methods
        """
        # Get the list of makers
        makers = [member for member in dir(self)
                  if member.startswith('make') and member != 'make_all']
        makers.sort()

        lines = []
        errors = []
        for maker_name in makers:
            maker = getattr(self, maker_name)
            try:
                # Store the result of the maker, if any
                content = maker(request)
                if content:
                    lines.append(content)

            except Exception as ex:
                errors.append('<li>Error calling {0}: {1}</li>' \
                              .format(maker_name, ex))

        if errors:
            # Add the errors part only if needed
            lines.append("<h2>Page generation errors</h2>\n<ul>"
                         "\n{errors}\n</ul>")

        return '\n'.join(lines)


    def make_basic(self, request):
        """
        Prints basic isolate information
        """
        lines = []
        lines.append('<dl>')

        for prop_var in sorted(dir(cohorte)):
            if prop_var.startswith('PROP'):
                key = getattr(cohorte, prop_var)
                lines.append('<dt>{0}</dt>\n<dd>{1}</dd>' \
                             .format(key, self._context.get_property(key)))

        lines.append('</dl>')

        return "<h2>Isolate informations</h2>\n{body}\n" \
            .format(body='\n'.join(lines))


    def make_bundles(self, request):
        """
        Lists the bundles installed
        """
        lines = []
        lines.append('<table>')
        lines.append('<tr>')
        lines.append('<th>Bundle ID</th>')
        lines.append('<th>Bundle Name</th>')
        lines.append('<th>Bundle State</th>')
        lines.append('</tr>')

        Bundle = pelix.framework.Bundle
        states = {Bundle.ACTIVE: 'ACTIVE',
                  Bundle.INSTALLED: 'INSTALLED',
                  Bundle.RESOLVED: 'RESOLVED',
                  Bundle.STARTING: 'STARTING',
                  Bundle.STOPPING: 'STOPPING',
                  Bundle.UNINSTALLED: 'UNINSTALLED'}

        for bundle in self._context.get_bundles():
            # New line
            lines.append('<tr>')
            lines.append('<td>{0}</td>'.format(bundle.get_bundle_id()))
            lines.append('<td>{0}</td>'.format(bundle.get_symbolic_name()))
            lines.append('<td>{0}</td>'.format(states.get(bundle.get_state(),
                                                          '<UNKNOWN>')))
            lines.append('</tr>')

        lines.append('</table>\n')
        return "<h2>Pelix bundles</h2>\n{table}\n" \
            .format(table='\n'.join(lines))


    def make_services(self, request):
        """
        Lists the services registered
        """
        lines = []
        lines.append('<table>')
        lines.append('<tr>')
        lines.append('<th>Service ID</th>')
        lines.append('<th>Service Ranking</th>')
        lines.append('<th>Specifications</th>')
        lines.append('<th>Bundle</th>')
        lines.append('<th>Properties</th>')
        lines.append('</tr>')

        for svc_ref in self._context.get_all_service_references(None, None):
            # New line
            lines.append('<tr>')

            # Important properties
            for name in (pelix.framework.SERVICE_ID,
                         pelix.framework.SERVICE_RANKING,
                         pelix.framework.OBJECTCLASS):
                lines.append('<td>{0}</td>'.format(svc_ref.get_property(name)))

            # Bundle
            bundle = svc_ref.get_bundle()
            lines.append('<td>{0} ({1})</td>'.format(bundle.get_symbolic_name(),
                                                     bundle.get_bundle_id()))

            # All properties
            lines.append('<td><dl>')
            for key, value in svc_ref.get_properties().items():
                lines.append('<dt>{0}</dt>\n<dd>{1}</dd>'.format(key, value))
            lines.append('</dl></td>')

            lines.append('</tr>')

        lines.append('</table>\n')
        return "<h2>Pelix services</h2>\n{table}\n" \
            .format(table='\n'.join(lines))


    def make_threads(self, request):
        """
        Prepares the section about process threads
        """
        # Get the current thread ID
        current_id = threading.current_thread().ident

        lines = []
        lines.append('<table>')
        lines.append('<tr>')
        lines.append('<th>Thread ID</th>')
        lines.append('<th>Thread Stack</th>')
        lines.append('</tr>')

        for thread_id, stack in sys._current_frames().items():
            # New line
            lines.append('<tr>')

            # Prepare the thread ID string
            if thread_id == current_id:
                suffix = " (current)"
            else:
                suffix = ""

            # Thread ID
            lines.append('<td>')
            lines.append("{0}{1}".format(thread_id, suffix))
            lines.append('</td>')

            # Prepare the stack string
            lines.append('<td><dl>')
            for filename, lineno, name, line in traceback.extract_stack(stack):
                # Line position
                stack_line = '<dt>{0}@{1}'.format(filename, lineno)
                if name:
                    stack_line += ' :: {0}(...)'.format(name)
                stack_line += '</dt>\n<dd>'

                if line:
                    # Line content
                    stack_line += '<pre>{0}</pre>'.format(line.strip())

                lines.append(stack_line + '</dd>')

            lines.append('</dl></tr>')

        lines.append('</table>')
        return "<h2>Threads</h2>\n{table}\n".format(table='\n'.join(lines))


    def do_GET(self, request, response):
        """
        Handles a GET request
        
        :param request: The HTTP request bean
        :param request: The HTTP response handler
        """
        query = request.get_path()[len(self._path) + 1:].split('/')
        action = query[0].lower()

        # To complete the page title
        subtitle = ""

        # Make the body
        if not action:
            content = self.make_all(request)

        else:
            maker = getattr(self, 'make_' + action, None)
            if not maker:
                content = self.make_all(request)

            else:
                subtitle = " - {0}".format(action)
                content = maker(request)

        # Make the HTML result
        page = """<html>
<head>
<title>COHORTE Debug{title_suffix}</title>
<style type="text/css">
{css}
</style>
</head>
<body>
<h1>COHORTE Debug{title_suffix}</h1>
{body}
</body>
</html>""".format(title_suffix=subtitle, css=CSS_STYLE, body=content)

        # Send the result
        response.send_content(200, page)


    @Validate
    def validate(self, context):
        """
        Component validated
        
        :param context: The bundle context
        """
        # Store the framework access
        self._context = context
        _logger.info("Debug servlet Ready")


    @Invalidate
    def invalidate(self, context):
        """
        Component invalidated
        
        :param context: The bundle context
        """
        # Clear the framework access
        self._context = None
        _logger.info("Debug servlet Gone")