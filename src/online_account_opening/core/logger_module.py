import logging
import os
from datetime import datetime

class LoggerManager:
    def __init__(self, log_name='app', log_file='app.log', level=logging.INFO):
        log_dir = os.path.join(os.path.dirname(__file__), '../../logs')
        os.makedirs(log_dir, exist_ok=True)

        log_path = os.path.join(log_dir, log_file)

        self.logger = logging.getLogger(log_name)
        self.logger.setLevel(level)

        if not self.logger.handlers:
            file_handler = logging.FileHandler(log_path, encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def log(self, message, level="info"):
        level = level.lower()
        if level == "debug":
            self.logger.debug(message)
        elif level == "warning":
            self.logger.warning(message)
        elif level == "error":
            self.logger.error(message)
        else:
            self.logger.info(message)
