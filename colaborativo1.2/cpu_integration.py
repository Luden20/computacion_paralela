import argparse
import os
import time
from concurrent.futures import ProcessPoolExecutor
from collections import Counter
from itertools import repeat
import sys
from dto import DnaAnalysis, ExecutionType


# This function process the data
# As parameters it gets the file output and a tuple that tells from where begin to read and where to end
def process_chunk(file, limits):
    start, end = limits
    local_dic = {"A": 0, "C": 0, "G": 0, "T": 0, "invalids": 0}
    valid_bytes = {
        65: "A",
        67: "C",
        71: "G",
        84: "T",
    }

    with open(file, 'rb') as input_file:
        if start > 0:
            input_file.seek(start - 1)
            input_file.readline()
        else:
            input_file.seek(0)

        while True:
            line_start = input_file.tell()
            if line_start >= end:
                break
            line = input_file.readline()
            if not line:
                break

            if not line:
                continue

            if line[0] == ord('>'):
                continue

            for byte in line:
                if byte in valid_bytes:
                    local_dic[valid_bytes[byte]] += 1
                elif byte not in (10, 13):
                    local_dic["invalids"] += 1

    return local_dic

# This function manage the parallel process by telling each process from where to read
def cpu_calculation(input_file_path, num_processes) -> DnaAnalysis:
    print("Calculating CPU...")
    if num_processes is None or num_processes <= 0:
        raise ValueError("num_processes must be greater than zero")

    file_size = os.path.getsize(input_file_path)
    if file_size == 0:
        return DnaAnalysis({"A": 0, "C": 0, "G": 0, "T": 0, "invalids": 0}, 0.0, ExecutionType.CPU)

    worker_count = min(num_processes, file_size)
    chunk_size = max(1, (file_size + worker_count - 1) // worker_count)
    chunks = [
        (offset, min(offset + chunk_size, file_size))
        for offset in range(0, file_size, chunk_size)
    ]
    final_dic = Counter()

    with ProcessPoolExecutor(max_workers=worker_count) as executor:
        start_total = time.perf_counter()
        results = executor.map(process_chunk, repeat(input_file_path), chunks)
        for res in results:
            final_dic.update(res)
        end_total = time.perf_counter()
    # We take the end time and calculate the duration
    time_taken = end_total - start_total
    return DnaAnalysis(dict(final_dic), time_taken, ExecutionType.CPU)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="File that needs to be analyzed", type=str)
    parser.add_argument("--processors", help="Amount of max processors", type=int)
    parser.add_argument("--iterative", action="store_true", help="Ejecuta modo iterativo")
    return parser.parse_args()

def iterative_benchmark(num_processors, actual_file):
    import matplotlib.pyplot as plt
    import numpy as np

    # We create empty list to add later the data
    processors = []
    times = []
    for i in range(1, num_processors):
        # We calculate for the i amount
        actual_time = cpu_calculation(actual_file, i)
        # We add to the list the data
        processors.append(i)
        times.append(actual_time.time)
    # We transform the data into arrays to make the graphs
    x = np.array(processors)
    y = np.array(times)
    # We build the plot
    plt.figure(figsize=(8, 5))
    plt.plot(x, y, marker='o')
    plt.xlabel("Processors")
    plt.ylabel("Time")
    plt.title("Data")
    plt.grid(True)
    # We save it as a png
    plt.savefig("grafica.png", dpi=300, bbox_inches="tight")
    plt.show()

    t1 = times[0]
    speedups = [t1 / t for t in times]
    efficiencies = [s / p for s, p in zip(speedups, processors)]
    sp = np.array(speedups)
    ef = np.array(efficiencies)

    # Speedup
    plt.figure(figsize=(8, 5))
    plt.plot(x, sp, marker='o', color='darkorange', label='Actual Speedup')
    plt.plot(x, x, linestyle='--', color='gray', label='Ideal Speedup')
    plt.xlabel("Processors")
    plt.ylabel("Speedup S(p)")
    plt.title("Speedup")
    plt.legend()
    plt.grid(True)
    plt.savefig("grafica_speedup.png", dpi=300, bbox_inches="tight")
    plt.show()

    # Eficiencia
    plt.figure(figsize=(8, 5))
    plt.plot(x, ef, marker='o', color='seagreen', label='Actual Efficiency')
    plt.axhline(y=1.0, linestyle='--', color='gray', label='Ideal Efficiency')
    plt.xlabel("Processors")
    plt.ylabel("Efficiency E(p)")
    plt.title("Efficiency")
    plt.ylim(0, 1.2)
    plt.legend()
    plt.grid(True)
    plt.savefig("grafica_efficiency.png", dpi=300, bbox_inches="tight")
    plt.show()

    sys.exit()
if __name__ == '__main__':
    args = get_args()
    if not args.iterative:
        print(cpu_calculation(args.file, int(args.processors)))
        sys.exit()
    iterative_benchmark(int(args.processors), args.file)
