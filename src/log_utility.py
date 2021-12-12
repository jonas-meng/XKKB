import logging


def config_logger(name, log_path):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(log_path)

    # Create formatters and add it to handlers
    c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    f_handler.setFormatter(f_format)
    c_handler.setFormatter(c_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    return logger
