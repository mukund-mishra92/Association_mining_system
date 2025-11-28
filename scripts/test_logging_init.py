import sys
from pprint import pprint
import logging

sys.path.append(r"c:\Users\Balmukund.Mishra\Desktop\NEO\association_mining_system")

from app.shared.utils.logger_config import setup_detailed_logging

files = setup_detailed_logging()
logging.getLogger().info("TEST: detailed logging forced via test script")

print("LOG_FILES:")
pprint(files)
