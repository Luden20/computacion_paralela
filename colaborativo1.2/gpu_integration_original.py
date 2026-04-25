import time

import argparse
import tempfile
from pathlib import Path
import numpy as np
import subprocess
from dto import DnaAnalysis, ExecutionType

try:
    import cupy as cp
except ImportError:
    cp = None


def gpu_support_status() -> tuple[bool, str]:
    if cp is None:
        return False, "CuPy no esta instalado en el entorno actual."
    try:
        _ = cp.cuda.runtime.getDeviceCount()
    except Exception as error:
        return False, f"No fue posible acceder a CUDA: {error}"
    return True, "GPU disponible."

def load_meta(meta_path):
    # We read rows and cols from the metadata file
    with open(meta_path, "r", encoding="utf-8") as f:
        rows = int(f.readline().strip())
        cols = int(f.readline().strip())
    return rows, cols


def load_bin_to_cuda(bin_path, meta_path):
    if cp is None:
        raise RuntimeError("CuPy no esta instalado. Activa el entorno correcto o instala la dependencia GPU.")

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

def gpu_alternative_calculation(filepath:str)->DnaAnalysis:
    available, message = gpu_support_status()
    if not available:
        raise RuntimeError(message)

    print("Calculating GPU...",flush=True)
    init_bytes=np.fromfile(filepath, dtype=np.uint8)
    gpu_bytes=cp.asarray(init_bytes)
    cp.cuda.Stream.null.synchronize()
    start_time = time.perf_counter()
    count_a = int(cp.count_nonzero(gpu_bytes == 65).item())
    count_c = int(cp.count_nonzero(gpu_bytes == 67).item())
    count_g = int(cp.count_nonzero(gpu_bytes == 71).item())
    count_t = int(cp.count_nonzero(gpu_bytes == 84).item())

    total_valid = count_a + count_c + count_g + count_t
    invalids = int(gpu_bytes.size - total_valid)
    count={
        "A": count_a,
        "C": count_c,
        "G": count_g,
        "T": count_t,
        "invalids": invalids
    }
    cp.cuda.Stream.null.synchronize()
    end_time=time.perf_counter()
    time_taken=end_time-start_time
    return DnaAnalysis(count,time_taken,ExecutionType.GPU)


def gpu_calculation(c_path, file_path) -> DnaAnalysis:
    available, message = gpu_support_status()
    if not available:
        raise RuntimeError(message)

    converter_path = str(Path(c_path).resolve())
    input_path = str(Path(file_path).resolve())
    print("Calculating GPU...")
    with tempfile.TemporaryDirectory(prefix="dna_gpu_") as temp_dir:
        result = subprocess.run(
            [converter_path, input_path],
            capture_output=True,
            text=True,
            check=True,
            cwd=temp_dir,
        )
        lines = result.stdout.strip().splitlines()
        if len(lines) < 2:
            raise RuntimeError(f"El convertidor no devolvio las rutas esperadas. stdout={result.stdout!r}")

        bin_path = lines[0]
        meta_path = lines[1]


        gpu_matrix = load_bin_to_cuda(bin_path, meta_path)

        
        cp.cuda.Stream.null.synchronize()
        start_time = time.perf_counter()
        counts = {
            "A": int(cp.sum(gpu_matrix == 65, dtype=cp.int64).item()),
            "C": int(cp.sum(gpu_matrix == 67, dtype=cp.int64).item()),
            "G": int(cp.sum(gpu_matrix == 71, dtype=cp.int64).item()),
            "T": int(cp.sum(gpu_matrix == 84, dtype=cp.int64).item())
        }
        counts["invalids"] = gpu_matrix.size - (counts["A"] + counts["C"] + counts["G"] + counts["T"])
        cp.cuda.Stream.null.synchronize()
    end_time = time.perf_counter()
    time_taken = end_time - start_time
    return DnaAnalysis(counts, time_taken, ExecutionType.GPU)

if __name__ == "__main__":
    print("Program started", flush=True)
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="File that needs to be analyzed", type=str)
    parser.add_argument("--converter-path", help="Executable path of the c program required", type=str, required=True)
    args = parser.parse_args()
    print(gpu_calculation(args.converter_path, args.file))
