import logging
from pythonjsonlogger import jsonlogger

def setup_structured_logging():
    """W9: Structured JSON Logging Setup"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Hapus default text handler mencegah logging dobel
    while logger.hasHandlers():
        logger.removeHandler(logger.handlers[0])
        
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(levelname)s %(name)s %(module)s %(message)s'
    )
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)
    return logger
