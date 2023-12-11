import logging


def setup_logger():
    _logger = logging.getLogger(__name__)
    _logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    _logger.addHandler(handler)
    return _logger


logger = setup_logger()
