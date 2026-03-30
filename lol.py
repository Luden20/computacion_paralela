import os
import time
from concurrent.futures import ProcessPoolExecutor
from collections import Counter
#definimos la ruta al archivo
input_file_path = 'GCA_000001405.29_GRCh38.p14_genomic.fna'
#deinimos el numero de procesos
num_processes = 28
#funcion individual para cada proceso que trabaja el archivo
def process_chunk(chunk_lines):
    local_dic = {}
    for line in chunk_lines:
        if isinstance(line, bytes):
            line = line.decode('ascii', errors='ignore')
        for char in line:
            if char in ("A", "C", "G", "T"):
                num = local_dic.get(char, 0)
                local_dic[char] = num + 1
    return local_dic

def write_chunks_in_parallel():
    start_total = time.perf_counter()
    
    with open(input_file_path, 'rb') as input_file:
        all_lines = input_file.readlines()
        num_lines = len(all_lines)
        lines_per_chunk = num_lines // num_processes
        chunks = [
            all_lines[i : i + lines_per_chunk] 
            for i in range(0, num_lines, lines_per_chunk)
        ]

        print(f"Iniciando {num_processes} procesos...")
        final_dic = Counter()
        
        with ProcessPoolExecutor(max_workers=num_processes) as executor:
            results = executor.map(process_chunk, chunks)
            for res in results:
                final_dic.update(res)
    end_total = time.perf_counter()
    print(f"Conteo final: {dict(final_dic)}")
    print(f"Tiempo total: {end_total - start_total:.2f} segundos")

if __name__ == '__main__':
    write_chunks_in_parallel()