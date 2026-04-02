import time

import argparse
import numpy as np
import cupy as cp
import subprocess
from dto import DnaAnalysis,ExecutionType

def load_meta(meta_path):
    # We read rows and cols from the metadata file
    with open(meta_path, "r", encoding="utf-8") as f:
        rows = int(f.readline().strip())
        cols = int(f.readline().strip())
    return rows, cols


def load_bin_to_cuda(bin_path, meta_path):
    # We load matrix shape from metadata
    rows, cols = load_meta(meta_path)

    # We read the raw binary file as uint8 on CPU
    cpu_array = np.fromfile(bin_path, dtype=np.uint8)

    expected_size = rows * cols
    if cpu_array.size != expected_size:
        raise ValueError(
            f"Binary size mismatch. Expected {expected_size} elements, got {cpu_array.size}"
        )

    # We reshape on CPU first
    cpu_matrix = cpu_array.reshape((rows, cols))

    gpu_matrix = cp.asarray(cpu_matrix)
    return gpu_matrix

def gpu_calculation(c_path, file_path)->DnaAnalysis:
    print("Calculating GPU...")
    start_time = time.perf_counter()
    result = subprocess.run(
        [c_path, file_path],
        capture_output=True,
        text=True,
    )
    lines = result.stdout.strip().splitlines()

    bin_path = lines[0]
    meta_path = lines[1]
    start_time=time.perf_counter()
    gpu_matrix = load_bin_to_cuda(bin_path, meta_path)
    counts = {
        "A": int(cp.sum(gpu_matrix == 65, dtype=cp.int64).item()),
        "C": int(cp.sum(gpu_matrix == 67, dtype=cp.int64).item()),
        "G": int(cp.sum(gpu_matrix == 71, dtype=cp.int64).item()),
        "T": int(cp.sum(gpu_matrix == 84, dtype=cp.int64).item())
    }
    counts["invalids"] = gpu_matrix.size - (counts["A"] + counts["C"] + counts["G"] + counts["T"])
    end_time = time.perf_counter()
    time_taken = end_time - start_time
    return DnaAnalysis(counts, time_taken,ExecutionType.GPU)

if __name__ == "__main__":
    print("Program started", flush=True)
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="File that needs to be analyzed", type=str)
    parser.add_argument("--converter-path", help="Executable path of the c program required", type=str, required=True)
    args = parser.parse_args()
    print(gpu_calculation(args.converter_path, args.file))
