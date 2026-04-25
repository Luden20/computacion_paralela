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


def gpu_calculation(c_path, file_path1, file_path2) -> DnaAnalysis:
    available, message = gpu_support_status()
    if not available:
        raise RuntimeError(message)

    converter_path = str(Path(c_path).resolve())

    def load_gpu_matrix(input_path):
        input_path = str(Path(input_path).resolve())

        result = subprocess.run(
            [converter_path, input_path],
            capture_output=True,
            text=True,
            check=True,
            cwd=tempfile.gettempdir(),
        )

        lines = result.stdout.strip().splitlines()
        if len(lines) < 2:
            raise RuntimeError(f"El convertidor no devolvio rutas válidas. stdout={result.stdout!r}")

        bin_path = lines[0]
        meta_path = lines[1]

        return load_bin_to_cuda(bin_path, meta_path)

    print("Calculating GPU...")

    # 🔹 Cargar ambas secuencias
    gpu_matrix1 = load_gpu_matrix(file_path1)
    gpu_matrix2 = load_gpu_matrix(file_path2)

    cp.cuda.Stream.null.synchronize()
    start_time = time.perf_counter()

    # 🔹 Conteo (puedes hacerlo solo para una si quieres)
    counts = {
        "A": int(cp.sum(gpu_matrix1 == 65, dtype=cp.int64).item()),
        "C": int(cp.sum(gpu_matrix1 == 67, dtype=cp.int64).item()),
        "G": int(cp.sum(gpu_matrix1 == 71, dtype=cp.int64).item()),
        "T": int(cp.sum(gpu_matrix1 == 84, dtype=cp.int64).item())
    }
    counts["invalids"] = gpu_matrix1.size - (
        counts["A"] + counts["C"] + counts["G"] + counts["T"]
    )

    # 🔥 COMPARACIÓN GPU
    min_len = min(gpu_matrix1.size, gpu_matrix2.size)

    comp = gpu_matrix1[:min_len] == gpu_matrix2[:min_len]

    matches = int(cp.sum(comp, dtype=cp.int64).item())
    mismatches = min_len - matches

    # considerar diferencia de longitud
    length_diff = abs(gpu_matrix1.size - gpu_matrix2.size)
    mismatches += length_diff

    similarity = matches / max(gpu_matrix1.size, gpu_matrix2.size) * 100

    cp.cuda.Stream.null.synchronize()
    end_time = time.perf_counter()

    time_taken = end_time - start_time

    return DnaAnalysis(
        counts=counts,
        time_taken=time_taken,
        execution_type=ExecutionType.GPU,
        matches=matches,
        mismatches=mismatches,
        similarity=similarity
    )

if __name__ == "__main__":
    print("Program started", flush=True)
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="File that needs to be analyzed", type=str)
    parser.add_argument("--converter-path", help="Executable path of the c program required", type=str, required=True)
    args = parser.parse_args()
    print(gpu_calculation(args.converter_path, args.file))
