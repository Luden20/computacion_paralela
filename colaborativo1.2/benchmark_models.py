from dataclasses import asdict, dataclass
from pathlib import Path

from dto import DnaAnalysis


@dataclass(slots=True)
class ResourceSample:
    timestamp: float
    cpu_percent: float
    rss_mb: float
    gpu_util_percent: float | None = None
    gpu_memory_mb: float | None = None


@dataclass(slots=True)
class ResourceUsage:
    avg_cpu_percent: float
    peak_cpu_percent: float
    peak_memory_mb: float
    avg_gpu_util_percent: float | None
    peak_gpu_util_percent: float | None
    peak_gpu_memory_mb: float | None
    samples: int


@dataclass(slots=True)
class BenchmarkRun:
    backend: str
    input_path: Path
    input_bases: int
    processors: int | None
    repeat: int
    analysis: DnaAnalysis
    resources: ResourceUsage

    @property
    def invalids_per_second(self) -> float:
        if self.analysis.time <= 0:
            return 0.0
        return self.analysis.result.get("invalids", 0) / self.analysis.time

    @property
    def bases_per_second(self) -> float:
        if self.analysis.time <= 0:
            return 0.0
        return self.input_bases / self.analysis.time

    def to_record(self) -> dict:
        record = {
            "backend": self.backend,
            "input_path": str(self.input_path),
            "input_bases": self.input_bases,
            "processors": self.processors,
            "repeat": self.repeat,
            "time_seconds": self.analysis.time,
            "bases_per_second": self.bases_per_second,
            "invalids": self.analysis.result.get("invalids", 0),
            "invalids_per_second": self.invalids_per_second,
            "count_A": self.analysis.result.get("A", 0),
            "count_C": self.analysis.result.get("C", 0),
            "count_G": self.analysis.result.get("G", 0),
            "count_T": self.analysis.result.get("T", 0),
        }
        record.update(asdict(self.resources))
        return record
