import os
import argparse
import time
from concurrent.futures import ProcessPoolExecutor
from collections import Counter
import matplotlib.pyplot as plt
import numpy as np
from itertools import repeat
import sys
from dto import DnaAnalysis,ExecutionType
# This function process the data
# As parameters it gets the file output and a tuple that tells from where begin to read and where to end
def process_chunk(file, limits):
    start, end = limits
    local_dic = {"A": 0, "C": 0, "G": 0, "T": 0, "invalids": 0}

    with open(file, 'rb') as input_file:
        for i, line in enumerate(input_file):
            if i < start:
                continue
            if i >= end:
                break

            if isinstance(line, bytes):
                line = line.decode('ascii', errors='ignore')

            if not line:
                continue

            if line[0] == '>':
                continue

            for char in line:
                if char in ("A", "C", "G", "T"):
                    local_dic[char] += 1
                elif char not in ("\n", "\r"):
                    local_dic["invalids"] += 1

    return local_dic

# This function manage the parallel process by telling each process from where to read
def cpu_calculation(input_file_path, num_processes)->DnaAnalysis:
    print("Calculating CPU...")
    num_lines = sum(1 for line in open(input_file_path))
    # We take the start time
    start_total = time.perf_counter()
    # We open the file in read mode
    with open(input_file_path, 'rb') as input_file:
        num_lines = sum(1 for _ in input_file)
        # // operator is 'the floor division operator'
        lines_per_chunk = num_lines // num_processes
        # We create a list of tuples with the (start,end) to work later
        chunks = [
            (i, min(i + lines_per_chunk, num_lines))
            for i in range(0, num_lines, lines_per_chunk)
        ]
        # We use Counter to accumulate values from our results
        final_dic = Counter()
        # We use a Process Pool to give each Process a function and parameters
        with ProcessPoolExecutor(max_workers=num_processes) as executor:
            # All the results ends in result
            results = executor.map(process_chunk, repeat(input_file_path), chunks)
            # We iterate in results and add it to the Counter() to consolidate the finall resullt
            for res in results:
                final_dic.update(res)
    # We take the end time and calculate the duration
    end_total = time.perf_counter()
    time_taken = end_total - start_total
    return DnaAnalysis(dict(final_dic), time_taken,ExecutionType.CPU)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="File that needs to be analyzed", type=str)
    parser.add_argument("--processors", help="Amount of max processors", type=int)
    parser.add_argument("--iterative", action="store_true", help="Ejecuta modo iterativo")
    return parser.parse_args()

def iterative_benchmark(num_processors, actual_file):
    # We create empty list to add later the data
    processors = []
    times = []
    for i in range(1, num_processors):
        # We calculate for the i amount
        actual_time = cpu_calculation(actual_file, i)
        # We add to the list the data
        processors.append(i)
        times.append(actual_time)
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
        cpu_calculation(int(args.processors), args.file)
        sys.exit()
    iterative_benchmark(int(args.processors), args.file)
