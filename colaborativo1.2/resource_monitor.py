import os
import subprocess
import threading
import time
from statistics import mean

import psutil

from benchmark_models import ResourceSample, ResourceUsage


def _safe_mean(values: list[float]) -> float | None:
    if not values:
        return None
    return mean(values)


class ResourceMonitor:
    def __init__(self, sample_interval: float = 0.2, enable_gpu: bool = False):
        self.sample_interval = sample_interval
        self.enable_gpu = enable_gpu
        self._process = psutil.Process(os.getpid())
        self._cpu_count = psutil.cpu_count() or 1
        self._samples: list[ResourceSample] = []
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._previous_cpu_total: float | None = None
        self._previous_timestamp: float | None = None

    def start(self) -> None:
        self._samples.clear()
        self._stop_event.clear()
        self._previous_cpu_total = None
        self._previous_timestamp = None
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> ResourceUsage:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join()
        return self._build_summary()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            self._samples.append(self._take_sample())
            self._stop_event.wait(self.sample_interval)
        self._samples.append(self._take_sample())

    def _take_sample(self) -> ResourceSample:
        timestamp = time.perf_counter()
        processes = self._alive_processes()
        cpu_total = 0.0
        rss_bytes = 0

        for process in processes:
            try:
                cpu_times = process.cpu_times()
                cpu_total += cpu_times.user + cpu_times.system
                rss_bytes += process.memory_info().rss
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        cpu_percent = 0.0
        if self._previous_cpu_total is not None and self._previous_timestamp is not None:
            elapsed = max(timestamp - self._previous_timestamp, 1e-9)
            cpu_percent = max(0.0, ((cpu_total - self._previous_cpu_total) / elapsed) * 100 / self._cpu_count)

        self._previous_cpu_total = cpu_total
        self._previous_timestamp = timestamp

        gpu_util, gpu_memory = self._query_gpu() if self.enable_gpu else (None, None)
        return ResourceSample(
            timestamp=timestamp,
            cpu_percent=cpu_percent,
            rss_mb=rss_bytes / (1024 * 1024),
            gpu_util_percent=gpu_util,
            gpu_memory_mb=gpu_memory,
        )

    def _alive_processes(self) -> list[psutil.Process]:
        processes = [self._process]
        try:
            processes.extend(self._process.children(recursive=True))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return processes
        return processes

    def _query_gpu(self) -> tuple[float | None, float | None]:
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=utilization.gpu,memory.used",
                    "--format=csv,noheader,nounits",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            return None, None

        line = result.stdout.strip().splitlines()[0]
        util_text, memory_text = [part.strip() for part in line.split(",", maxsplit=1)]
        return float(util_text), float(memory_text)

    def _build_summary(self) -> ResourceUsage:
        cpu_values = [sample.cpu_percent for sample in self._samples]
        rss_values = [sample.rss_mb for sample in self._samples]
        gpu_util_values = [sample.gpu_util_percent for sample in self._samples if sample.gpu_util_percent is not None]
        gpu_memory_values = [sample.gpu_memory_mb for sample in self._samples if sample.gpu_memory_mb is not None]

        return ResourceUsage(
            avg_cpu_percent=_safe_mean(cpu_values) or 0.0,
            peak_cpu_percent=max(cpu_values, default=0.0),
            peak_memory_mb=max(rss_values, default=0.0),
            avg_gpu_util_percent=_safe_mean(gpu_util_values),
            peak_gpu_util_percent=max(gpu_util_values, default=None),
            peak_gpu_memory_mb=max(gpu_memory_values, default=None),
            samples=len(self._samples),
        )
