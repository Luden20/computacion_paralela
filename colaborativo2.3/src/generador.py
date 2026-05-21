import argparse
import os
import time
from pathlib import Path

BASES = b"ATCG"

def create_translation_table():
    source = bytes(range(256))
    target = bytes(BASES[value & 3] for value in range(256))
    return bytes.maketrans(source, target)

def generate_dna_file(output_path, size_mb, block_mb):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total_bytes = size_mb * 1024 * 1024
    block_size = block_mb * 1024 * 1024
    remaining = total_bytes

    table = create_translation_table()
    start_time = time.perf_counter()

    with open(output_path, "wb") as file:
        while remaining > 0:
            current_size = min(block_size, remaining)
            block = os.urandom(current_size).translate(table)
            file.write(block)
            remaining -= current_size

    elapsed = time.perf_counter() - start_time

    print(f"Archivo generado: {output_path}")
    print(f"Tamaño generado: {total_bytes:,} bytes")
    print(f"Tiempo de generación: {elapsed:.2f} segundos")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--size-mb", type=int, default=1024)
    parser.add_argument("--block-mb", type=int, default=4)
    args = parser.parse_args()

    generate_dna_file(args.output, args.size_mb, args.block_mb)

if __name__ == "__main__":
    main()