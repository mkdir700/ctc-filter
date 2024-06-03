from ctc_filter.config import settings
from ctc_filter.downloader.downloader import Downloader


class Execution:
    def __init__(self, exchange):
        self.ctc_filter = ctc_filter
        self.downloader = Downloader()

    def run(self, data):
        ...
