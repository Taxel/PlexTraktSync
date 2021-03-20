import logging
from .config import CONFIG
from .path import log_file

log_level = logging.DEBUG if CONFIG['log_debug_messages'] else logging.INFO
logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',
                    handlers=[logging.FileHandler(log_file, 'w', 'utf-8')],
                    level=log_level)
