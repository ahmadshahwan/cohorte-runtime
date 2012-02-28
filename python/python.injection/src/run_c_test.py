#!/usr/bin/python3
#-- Content-Encoding: UTF-8 --

from psem2m.services import pelix
from psem2m.services.pelix import Framework
import logging
import time

# ------------------------------------------------------------------------------

# Set logging level
logging.basicConfig(level=logging.DEBUG)

# ------------------------------------------------------------------------------

logging.info("--- Start Pelix ---")
framework = pelix.FrameworkFactory.get_framework({'debug': True})
assert isinstance(framework, Framework)

logging.info("-- Install iPOPO --")
bid = framework.install_bundle("psem2m.component.ipopo")
bundle = framework.get_bundle_by_id(bid)
bundle.start()

logging.info("-- Install run_c_test --")
bid = framework.install_bundle("c_test")
logging.info("> Bundle ID : %d", bid)
bundle = framework.get_bundle_by_id(bid)
bundle.start()

# For interactive mode
bc = framework.get_bundle_context()

def stop():
    logging.info("--- Stop Pelix ---")
    framework.stop()

# For execution mode
time.sleep(3)

start = time.time()
stop()
end = time.time()

logging.info("--- Time to stop the framework : %.2f sec", (end - start))