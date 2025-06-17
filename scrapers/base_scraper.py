from abc import ABC, abstractmethod

class BaseScraper(ABC):
    def __init__(self, driver, logger):
        self.driver = driver
        self.logger = logger

    @abstractmethod
    def scrape(self):
        pass
