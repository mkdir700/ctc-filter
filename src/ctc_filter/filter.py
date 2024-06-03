from abc import ABC, abstractmethod

from pandas import DataFrame


class Filter(ABC):
    name: str = "Filter Name"
    description: str = "Filter Description"

    def __init__(self, df: DataFrame) -> None:
        self.df = df

    @abstractmethod
    def filter(self) -> bool:
        ...
