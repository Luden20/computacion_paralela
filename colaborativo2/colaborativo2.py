import argparse
import os

from cpu_integration import cpu_calculation
from gpu_integration import gpu_calculation
from benchmark_runner import run_benchmarks

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="File that needs to be analyzed", type=str)
    parser.add_argument("--processors", help="Amount of max processors", type=int, default=os.cpu_count() or 1)
    parser.add_argument("--converter-path", help="Executable path of the c program required", type=str, required=True)
    parser.add_argument("--benchmark", action="store_true", help="Ejecuta benchmark CPU vs GPU usando el archivo completo.")
    parser.add_argument("--benchmark-repeats", type=int, default=1, help="Cantidad de repeticiones del benchmark.")
    parser.add_argument("--benchmark-output-dir", type=str, default="benchmark_artifacts", help="Directorio donde se guardan CSV y graficas.")
    return parser.parse_args()
if __name__ == "__main__":
    args = get_args()
    if args.benchmark:
        run_benchmarks(
            file_path=args.file,
            converter_path=args.converter_path,
            processors=args.processors,
            repeats=args.benchmark_repeats,
            output_dir=args.benchmark_output_dir,
        )
        raise SystemExit(0)
    cpu_result = cpu_calculation(args.file, args.processors)
    print(cpu_result)
    #gpu_result=gpu_alternative_calculation(args.file)
    gpu_result = gpu_calculation(args.converter_path, args.file)
    print(gpu_result)
