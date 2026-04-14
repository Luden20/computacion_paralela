import time
import argparse
import tempfile
from pathlib import Path
import numpy as np
import subprocess
from enum import Enum
from dataclasses import dataclass
import cupy as cp


class ExecutionType(Enum):
    CPU = "CPU"
    GPU = "GPU"

@dataclass
class DnaComparison:
    total_differences: int
    time_taken: float
    execution_type: ExecutionType



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

def gpu_alternative_calculation(filepath:str)->DnaComparison:
    pass

def gpu_calculation(c_path, file_path1, file_path2) -> DnaComparison:
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

    # Cargar ambas secuencias
    gpu_matrix1 = load_gpu_matrix(file_path1)
    gpu_matrix2 = load_gpu_matrix(file_path2)

    cp.cuda.Stream.null.synchronize()
    start_time = time.perf_counter()

    # Conteo
    counts = {
        "A": int(cp.sum(gpu_matrix1 == 65, dtype=cp.int64).item()),
        "C": int(cp.sum(gpu_matrix1 == 67, dtype=cp.int64).item()),
        "G": int(cp.sum(gpu_matrix1 == 71, dtype=cp.int64).item()),
        "T": int(cp.sum(gpu_matrix1 == 84, dtype=cp.int64).item())
    }
    counts["invalids"] = gpu_matrix1.size - (
        counts["A"] + counts["C"] + counts["G"] + counts["T"]
    )

    # 🔥 COMPARACIÓN EN FORMA DE MATRIZ GPU
    min_len = min(gpu_matrix1.size, gpu_matrix2.size)

    # Creamos una matriz booleana donde los caracteres son distintos
    mismatch_matrix = (gpu_matrix1[:min_len] != gpu_matrix2[:min_len])
    
    # Sumamos rápidamente todos los booleanos (True = 1) para contar las diferencias
    mismatches = int(cp.sum(mismatch_matrix, dtype=cp.int64).item())

    # considerar diferencia de longitud como diferencias adicionales
    length_diff = abs(gpu_matrix1.size - gpu_matrix2.size)
    total_differences = mismatches + length_diff

    cp.cuda.Stream.null.synchronize()
    end_time = time.perf_counter()

    time_taken = end_time - start_time

    return DnaComparison(
        total_differences=total_differences,
        time_taken=time_taken,
        execution_type=ExecutionType.GPU
    )

if __name__ == "__main__":
    print("Program started", flush=True)

    parser = argparse.ArgumentParser()
    
    parser.add_argument("--file1", help="First DNA file", type=str, required=True)
    parser.add_argument("--file2", help="Second DNA file", type=str, required=True)
    parser.add_argument(
        "--converter-path",
        help="Executable path of the C program required",
        type=str,
        required=True
    )

    args = parser.parse_args()

    print(gpu_calculation(args.converter_path, args.file1, args.file2))
