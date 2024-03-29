import logging


class Logger:
    def __init__(self, logname: str, filename: str) -> None:
        self.logger = logging.getLogger(logname)
        self.logger.setLevel(logging.INFO)
        self.handler = logging.FileHandler(filename,'a')
        self.handler.setLevel(logging.INFO)
        self.formatter = logging.Formatter('%(name)s: %(message)s', datefmt='%H:%M:%S')
        self.handler.setFormatter(self.formatter)
        self.logger.addHandler(self.handler)