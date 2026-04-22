import argparse
import json
import math
import os
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from itertools import repeat
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "resultados"


def ensure_output_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def build_json_output_path(num_processes):
    return ensure_output_dir() / f"conteo_final_{num_processes}p.json"


def save_counts_json(result, num_processes):
    output_path = build_json_output_path(num_processes)
    with output_path.open("w", encoding="utf-8") as json_file:
        json.dump(result, json_file, indent=2)
    print(f"JSON guardado en: {output_path}")
    return output_path


# This function process the data
# As parameters it gets the file output and a tuple that tells from where begin to read and where to end
def process_chunk(file, limits):
    start, end = limits
    local_dic = {}
    with open(file, 'rb') as input_file:
        for i, line in enumerate(input_file):
            #This make sure we only process within the range
            if i < start:
                continue
            if i >= end:
                break
            #We make sure the 'line' is in ascii codification
            if isinstance(line, bytes):
                line = line.decode('ascii', errors='ignore')
            #We skipe the headers
            if line[0]=='>':
                continue
            #We iterate char by char to make sure if it is in the valid chars we are looking for
            for char in line:
                if char in ("A", "C", "G", "T"):
                    num = local_dic.get(char, 0)
                    local_dic[char] = num + 1
    return local_dic
# This function manage the parallel process by telling each process from where to read
def write_chunks_in_parallel(input_file_path, num_processes):
    # We take the start time
    start_total = time.perf_counter()

    # We open the file in read mode
    with open(input_file_path, 'rb') as input_file:
        num_lines = len(input_file.readlines())

        if num_lines == 0:
            final_result = {}
            print("Conteo final: {}")
            save_counts_json(final_result, num_processes)
            time_taken = time.perf_counter() - start_total
            print(f"{num_processes} p: {time_taken} s")
            return time_taken

        actual_workers = min(num_processes, num_lines)
        lines_per_chunk = math.ceil(num_lines / actual_workers)
        # We create a list of tuples with the (start,end) to work later
        chunks = [
            (i, min(i + lines_per_chunk, num_lines))
            for i in range(0, num_lines, lines_per_chunk)
        ]
        # We use Counter to accumulate values from our results
        final_dic = Counter()
        # We use a Process Pool to give each Process a function and parameters
        with ProcessPoolExecutor(max_workers=actual_workers) as executor:
            # All the results ends in result
            results = executor.map(process_chunk, repeat(input_file_path), chunks)
            # We iterate in results and add it to the Counter() to consolidate the final result
            for res in results:
                final_dic.update(res)

    # We take the end time and calculate the duration
    end_total = time.perf_counter()
    final_result = dict(final_dic)
    print(f"Conteo final: {final_result}")
    save_counts_json(final_result, num_processes)
    time_taken = end_total - start_total
    print(f"{num_processes} p: {time_taken} s")
    return time_taken


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="File that needs to be analyzed", type=str)
    parser.add_argument("--processors", help="Amount of max processors", type=int)
    parser.add_argument("--iterative", action="store_true", help="Ejecuta modo iterativo")
    return parser.parse_args()


if __name__ == '__main__':
    args = get_args()
    num_processors = int(args.processors)
    actual_file = str(args.file)
    iterative = args.iterative

    # If we don't add --iterative we just execute once with the num_processors indicated
    if not iterative:
        print(f"one call with {num_processors} processors")
        write_chunks_in_parallel(actual_file, num_processors)
        sys.exit()

    # If not we do the benchmarking

    import matplotlib.pyplot as plt
    import numpy as np

    output_dir = ensure_output_dir()

    # We create empty list to add later the data
    processors=[]
    times=[]
    for i in range(1, num_processors + 1):
        # We calculate for the i amount
        actual_time = write_chunks_in_parallel(actual_file, i)
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
    plt.savefig(output_dir / "grafica.png", dpi=300, bbox_inches="tight")
    plt.close()

    t1 = times[0]
    speedups     = [t1 / t for t in times]
    efficiencies = [s / p for s, p in zip(speedups, processors)]
    sp = np.array(speedups)
    ef = np.array(efficiencies)
 
    # Speedup
    plt.figure(figsize=(8, 5))
    plt.plot(x, sp, marker='o', color='darkorange', label='Actual Speedup')
    plt.plot(x, x,  linestyle='--', color='gray', label='Ideal Speedup')
    plt.xlabel("Processors")
    plt.ylabel("Speedup S(p)")
    plt.title("Speedup")
    plt.legend()
    plt.grid(True)
    plt.savefig(output_dir / "grafica_speedup.png", dpi=300, bbox_inches="tight")
    plt.close()

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
    plt.savefig(output_dir / "grafica_efficiency.png", dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Graficas guardadas en: {output_dir}")

    sys.exit()
