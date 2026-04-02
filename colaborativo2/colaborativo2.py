import argparse
import os

from analysis_output import print_analysis, serialize_analysis, write_combined_analysis
from cpu_integration import cpu_calculation
from gpu_integration import gpu_calculation


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="File that needs to be analyzed", type=str)
    parser.add_argument("--processors", help="Amount of max processors", type=int, default=os.cpu_count() or 1)
    parser.add_argument("--converter-path", help="Executable path of the c program required", type=str, required=True)
    parser.add_argument("--output-dir", help="Directorio donde se guardan los JSON de salida.", type=str, default="analysis_outputs")
    parser.add_argument("--analysis-output-dir", help="Directorio donde se guardan los JSON de analisis durante benchmark.", type=str, default="analysis_outputs")
    parser.add_argument("--benchmark", action="store_true", help="Ejecuta benchmark CPU vs GPU usando el archivo completo.")
    parser.add_argument("--benchmark-repeats", type=int, default=1, help="Cantidad de repeticiones del benchmark.")
    parser.add_argument("--benchmark-output-dir", type=str, default="benchmark_artifacts", help="Directorio donde se guardan CSV y graficas.")
    return parser.parse_args()
if __name__ == "__main__":
    args = get_args()
    if args.benchmark:
        from benchmark_runner import run_benchmarks

        run_benchmarks(
            file_path=args.file,
            converter_path=args.converter_path,
            processors=args.processors,
            repeats=args.benchmark_repeats,
            output_dir=args.benchmark_output_dir,
            analysis_output_dir=args.analysis_output_dir,
        )
        raise SystemExit(0)
    cpu_result = cpu_calculation(args.file, args.processors)
    print_analysis(cpu_result)
    gpu_result = gpu_calculation(args.converter_path, args.file)
    print_analysis(gpu_result)
    write_combined_analysis(
        analyses={
            "cpu": serialize_analysis(cpu_result),
            "gpu": serialize_analysis(gpu_result),
        },
        input_file=args.file,
        output_dir=args.output_dir,
    )
