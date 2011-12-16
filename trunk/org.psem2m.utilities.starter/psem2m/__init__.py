#!/usr/bin/python3
#-- Content-Encoding: utf-8 --
"""
Common classes, methods and constants for the PSEM2M scripts

@author: Thomas Calmant
"""

import sys

# ------------------------------------------------------------------------------

# Java home directory
JAVA_HOME = "JAVA_HOME"

# PSEM2M Home directory environment variable
PSEM2M_HOME = "PSEM2M_HOME"

# PSEM2M Base directory environment variable
PSEM2M_BASE = "PSEM2M_BASE"

# ------------------------------------------------------------------------------

class PSEM2MException(Exception):
    """
    Base class for PSEM2M exceptions
    """
    pass