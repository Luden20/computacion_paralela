import argparse
import json
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import numpy as np

try:
    import cupy as cp
except ImportError:
    cp = None


DIFFERENCES_JSON_PATH = Path("differences.json")
EXECUTION_TIME_JSON_PATH = Path("execution_time.json")
PROGRESS_STEP = 10
MAX_BATCH_LINES = 16384
MAX_BATCH_CHARS = 8 * 1024 * 1024


class ExecutionType(Enum):
    CPU = "CPU"
    GPU = "GPU"


@dataclass
class DnaComparison:
    total_differences: int
    time_taken: float
    execution_type: ExecutionType


@dataclass
class ComparableBatchLine:
    byte_position: int
    line1: bytes
    line2: bytes


def gpu_support_status() -> tuple[bool, str]:
    if cp is None:
        return False, "CuPy no esta instalado en el entorno actual."
    try:
        device_count = cp.cuda.runtime.getDeviceCount()
    except Exception as error:
        return False, f"No fue posible acceder a CUDA: {error}"
    if device_count <= 0:
        return False, "No se detectaron dispositivos CUDA disponibles."
    return True, f"GPU disponible. Dispositivos detectados: {device_count}."


def trim_line_ending(raw_line: bytes) -> bytes:
    if raw_line.endswith(b"\n"):
        raw_line = raw_line[:-1]
    if raw_line.endswith(b"\r"):
        raw_line = raw_line[:-1]
    return raw_line


def json_char_or_null(value: int | None) -> str:
    if value is None:
        return "null"
    return json.dumps(chr(value), ensure_ascii=False)


def report_stage(stage_number: int, total_stages: int, message: str) -> None:
    print(f"[ETAPA {stage_number}/{total_stages}] {message}", flush=True)


def report_progress(percent: int, compared_lines: int, total_differences: int) -> None:
    print(
        f"Progreso: {percent}% | lineas comparables: {compared_lines} | diferencias acumuladas: {total_differences}",
        flush=True,
    )


def write_difference(
    output_file,
    first_entry: bool,
    byte_position: int,
    column_index: int,
    char1: int | None,
    char2: int | None,
) -> bool:
    if not first_entry:
        output_file.write(",\n")
    else:
        first_entry = False

    output_file.write(
        f"[{byte_position},{column_index},{json_char_or_null(char1)},{json_char_or_null(char2)}]"
    )
    return first_entry


def compare_batch_on_gpu(batch: list[ComparableBatchLine], output_file, first_entry: bool) -> tuple[int, bool]:
    if not batch:
        return 0, first_entry

    batch_size = len(batch)
    lengths1 = np.fromiter((len(item.line1) for item in batch), dtype=np.int32, count=batch_size)
    lengths2 = np.fromiter((len(item.line2) for item in batch), dtype=np.int32, count=batch_size)
    max_len = int(max(lengths1.max(initial=0), lengths2.max(initial=0)))

    if max_len == 0:
        return 0, first_entry

    cpu_matrix1 = np.zeros((batch_size, max_len), dtype=np.uint8)
    cpu_matrix2 = np.zeros((batch_size, max_len), dtype=np.uint8)

    for row_index, item in enumerate(batch):
        if lengths1[row_index] > 0:
            cpu_matrix1[row_index, : lengths1[row_index]] = np.frombuffer(item.line1, dtype=np.uint8)
        if lengths2[row_index] > 0:
            cpu_matrix2[row_index, : lengths2[row_index]] = np.frombuffer(item.line2, dtype=np.uint8)

    gpu_matrix1 = cp.asarray(cpu_matrix1)
    gpu_matrix2 = cp.asarray(cpu_matrix2)
    gpu_lengths1 = cp.asarray(lengths1)
    gpu_lengths2 = cp.asarray(lengths2)
    column_indexes = cp.arange(max_len, dtype=cp.int32)

    valid1 = column_indexes < gpu_lengths1[:, None]
    valid2 = column_indexes < gpu_lengths2[:, None]
    mismatch_mask = (valid1 != valid2) | ((gpu_matrix1 != gpu_matrix2) & valid1 & valid2)

    mismatch_rows, mismatch_cols = cp.nonzero(mismatch_mask)
    mismatch_rows_cpu = cp.asnumpy(mismatch_rows)
    mismatch_cols_cpu = cp.asnumpy(mismatch_cols)
    diff_count = int(mismatch_rows_cpu.size)

    for row_index, column_index in zip(mismatch_rows_cpu.tolist(), mismatch_cols_cpu.tolist()):
        batch_item = batch[row_index]
        char1 = batch_item.line1[column_index] if column_index < len(batch_item.line1) else None
        char2 = batch_item.line2[column_index] if column_index < len(batch_item.line2) else None
        first_entry = write_difference(
            output_file,
            first_entry,
            batch_item.byte_position,
            column_index,
            char1,
            char2,
        )

    del gpu_matrix1, gpu_matrix2, gpu_lengths1, gpu_lengths2, column_indexes
    del valid1, valid2, mismatch_mask, mismatch_rows, mismatch_cols

    return diff_count, first_entry


def build_execution_summary(file_path1: str, file_path2: str, result: DnaComparison) -> dict:
    return {
        "file1": file_path1,
        "file2": file_path2,
        "time_taken": result.time_taken,
        "total_differences": result.total_differences,
    }


def gpu_calculation(*args) -> DnaComparison:
    if len(args) == 2:
        converter_path = None
        file_path1, file_path2 = args
    elif len(args) == 3:
        converter_path, file_path1, file_path2 = args
    else:
        raise TypeError(
            "gpu_calculation espera (file_path1, file_path2) o (converter_path, file_path1, file_path2)."
        )

    total_stages = 4
    report_stage(1, total_stages, "Validando entorno CUDA/CuPy...")
    available, message = gpu_support_status()
    if not available:
        raise RuntimeError(message)
    print(message, flush=True)

    if converter_path:
        print(
            "Aviso: --converter-path se conserva por compatibilidad, pero la ruta GPU exacta ya no lo necesita.",
            flush=True,
        )

    input_path1 = Path(file_path1).resolve()
    input_path2 = Path(file_path2).resolve()

    if not input_path1.exists() or not input_path2.exists():
        raise FileNotFoundError("Uno de los archivos especificados no existe.")

    size1 = input_path1.stat().st_size
    size2 = input_path2.stat().st_size
    max_size = max(size1, size2, 1)

    report_stage(2, total_stages, "Preparando salida JSON y lectura en streaming...")

    compared_lines = 0
    total_differences = 0
    last_reported_percent = -1
    first_entry = True
    current_batch: list[ComparableBatchLine] = []
    current_batch_chars = 0

    report_stage(3, total_stages, "Comparando bloques en GPU y escribiendo differences.json...")
    cp.cuda.Stream.null.synchronize()
    start_time = time.perf_counter()

    with input_path1.open("rb") as file1, input_path2.open("rb") as file2, DIFFERENCES_JSON_PATH.open(
        "w",
        encoding="utf-8",
    ) as differences_json:
        differences_json.write("[\n")

        while True:
            raw_line1 = file1.readline()
            raw_line2 = file2.readline()

            if not raw_line1 and not raw_line2:
                break

            line1 = trim_line_ending(raw_line1) if raw_line1 else b""
            line2 = trim_line_ending(raw_line2) if raw_line2 else b""

            if (line1 and line1.startswith(b">")) or (line2 and line2.startswith(b">")):
                current_percent = int((max(file1.tell(), file2.tell()) * 100) / max_size)
                if current_percent >= last_reported_percent + PROGRESS_STEP:
                    current_percent = min(100, (current_percent // PROGRESS_STEP) * PROGRESS_STEP)
                    if current_percent > last_reported_percent:
                        report_progress(current_percent, compared_lines, total_differences)
                        last_reported_percent = current_percent
                continue

            current_batch.append(
                ComparableBatchLine(
                    byte_position=file1.tell(),
                    line1=line1,
                    line2=line2,
                )
            )
            compared_lines += 1
            current_batch_chars += max(len(line1), len(line2))

            should_flush = (
                len(current_batch) >= MAX_BATCH_LINES or current_batch_chars >= MAX_BATCH_CHARS
            )
            if should_flush:
                batch_differences, first_entry = compare_batch_on_gpu(
                    current_batch,
                    differences_json,
                    first_entry,
                )
                total_differences += batch_differences
                current_batch.clear()
                current_batch_chars = 0

                current_percent = int((max(file1.tell(), file2.tell()) * 100) / max_size)
                current_percent = min(100, current_percent)
                if current_percent >= last_reported_percent + PROGRESS_STEP:
                    current_percent = (current_percent // PROGRESS_STEP) * PROGRESS_STEP
                    if current_percent > last_reported_percent:
                        report_progress(current_percent, compared_lines, total_differences)
                        last_reported_percent = current_percent

        if current_batch:
            batch_differences, first_entry = compare_batch_on_gpu(
                current_batch,
                differences_json,
                first_entry,
            )
            total_differences += batch_differences

        differences_json.write("\n]\n")

    cp.cuda.Stream.null.synchronize()
    end_time = time.perf_counter()
    time_taken = end_time - start_time

    if last_reported_percent < 100:
        report_progress(100, compared_lines, total_differences)

    report_stage(4, total_stages, "Generando execution_time.json y resumen final...")
    result = DnaComparison(
        total_differences=total_differences,
        time_taken=time_taken,
        execution_type=ExecutionType.GPU,
    )

    with EXECUTION_TIME_JSON_PATH.open("w", encoding="utf-8") as time_json:
        json.dump(build_execution_summary(str(input_path1), str(input_path2), result), time_json, indent=4)

    return result


def parse_args():
    parser = argparse.ArgumentParser(description="Comparador de ADN con GPU (CuPy)")
    parser.add_argument("--file1", help="First DNA file", type=str, required=True)
    parser.add_argument("--file2", help="Second DNA file", type=str, required=True)
    parser.add_argument(
        "--converter-path",
        help="Ruta del convertidor C legado. Se mantiene solo por compatibilidad, ya no es necesario.",
        type=str,
        required=False,
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    try:
        result = gpu_calculation(args.file1, args.file2)

        print("\n" + "=" * 40)
        print("RESULTADOS DE LA COMPARACION")
        print("=" * 40)
        print(f"Archivo 1: {Path(args.file1).name}")
        print(f"Archivo 2: {Path(args.file2).name}")
        print(f"Tiempo total: {result.time_taken:.4f} segundos")
        print(f"Total de diferencias: {result.total_differences}")
        print(
            "\nArchivos 'differences.json' y 'execution_time.json' generados y actualizados correctamente.",
            flush=True,
        )
    except Exception as error:
        print(f"Error durante la ejecucion: {error}", flush=True)
        raise
