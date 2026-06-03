import argparse
import json
import time
from pathlib import Path


def count_patterns(payload, original_len, patterns):
    result = {}

    for pattern in patterns:
        count = 0
        start = 0

        while True:
            pos = payload.find(pattern, start)

            if pos == -1 or pos >= original_len:
                break

            count += 1
            start = pos + 1

        result[pattern.decode()] = count

    return result


def process_chunk(offset, payload, original_len, patterns):
    core = payload[:original_len]

    base_counts = {
        "A": core.count(b"A"),
        "T": core.count(b"T"),
        "C": core.count(b"C"),
        "G": core.count(b"G"),
    }

    total_known = sum(base_counts.values())
    other = original_len - total_known

    return {
        "offset": offset,
        "length": original_len,
        "base_counts": base_counts,
        "other": other,
        "pattern_counts": count_patterns(payload, original_len, patterns),
    }


def reduce_results(results, patterns):
    final_bases = {"A": 0, "T": 0, "C": 0, "G": 0}
    final_patterns = {pattern.decode(): 0 for pattern in patterns}
    total_other = 0
    total_length = 0

    for result in results:
        total_length += result["length"]
        total_other += result["other"]

        for base, value in result["base_counts"].items():
            final_bases[base] += value

        for pattern, value in result["pattern_counts"].items():
            final_patterns[pattern] += value

    return final_bases, final_patterns, total_other, total_length


def procesar(
    input, patterns="ATGCGT,TATA,GATTACA", chunk_mb=32, output="results/secuencial.json"
):
    input_path = Path(input)
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    patterns_list = [
        pattern.strip().upper().encode()
        for pattern in patterns.split(",")
        if pattern.strip()
    ]
    if not patterns_list:
        raise ValueError("Debe indicar al menos un patrón.")

    max_pattern_len = max(len(pattern) for pattern in patterns_list)
    overlap = max_pattern_len - 1

    chunk_size = chunk_mb * 1024 * 1024
    file_size = input_path.stat().st_size

    results = []
    start_time = time.perf_counter()

    with open(input_path, "rb") as file:
        for offset in range(0, file_size, chunk_size):
            original_len = min(chunk_size, file_size - offset)
            read_len = min(original_len + overlap, file_size - offset)

            file.seek(offset)
            payload = file.read(read_len)

            results.append(process_chunk(offset, payload, original_len, patterns_list))

    elapsed = time.perf_counter() - start_time

    final_bases, final_patterns, total_other, total_length = reduce_results(
        results, patterns_list
    )

    report = {
        "mode": "sequential",
        "file": str(input_path),
        "file_size_bytes": file_size,
        "chunk_size_bytes": chunk_size,
        "chunks": len(results),
        "patterns": [pattern.decode() for pattern in patterns_list],
        "elapsed_seconds": elapsed,
        "base_counts": final_bases,
        "pattern_counts": final_patterns,
        "other_symbols": total_other,
        "total_processed_symbols": total_length,
    }

    with open(output_path, "w") as file:
        json.dump(report, file, indent=4)

    print(json.dumps(report, indent=4))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--patterns", default="ATGCGT,TATA,GATTACA")
    parser.add_argument("--chunk-mb", type=int, default=32)
    args = parser.parse_args()

    procesar(
        input=args.input,
        patterns=args.patterns,
        chunk_mb=args.chunk_mb,
    )
