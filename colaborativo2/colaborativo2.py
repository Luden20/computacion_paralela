import argparse
from cpu_integration import cpu_calculation
from gpu_integration import gpu_calculation

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="File that needs to be analyzed", type=str)
    parser.add_argument("--processors", help="Amount of max processors", type=int)
    parser.add_argument("--converter-path", help="Executable path of the c program required", type=str, required=True)
    return parser.parse_args()
if __name__ == "__main__":
    args = get_args()

    cpu_result = cpu_calculation(args.file, args.processors)
    print(cpu_result)

    gpu_result = gpu_calculation(args.converter_path, args.file)
    print(gpu_result)