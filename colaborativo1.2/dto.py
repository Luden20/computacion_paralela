from dataclasses import dataclass
from enum import Enum


class ExecutionType(Enum):
    GPU="GPU"
    CPU="CPU"

@dataclass
class DnaAnalysis:
    result:dict
    time:float
    type:ExecutionType
    def __str__(self):
        return f"{'-'*10}\n{self.type} calculation \n result={str(dict(sorted(self.result.items())))}\n With time {self.time}\n{'-'*10}"