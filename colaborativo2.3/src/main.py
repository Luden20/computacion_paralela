import argparse
import ray
import time
import secuential_process
import paralel_cluster_process
def buildArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--patterns", default="ATGCGT,TATA,GATTACA")
    parser.add_argument("--chunk-mb", type=int, default=32)
    parser.add_argument("--output", default="results/distribuido.json")
    parser.add_argument("--max-inflight", type=int, default=0)
    parser.add_argument("--ray-address", default="auto")
    args = parser.parse_args()
    return args
def obtenerNucleos( ray_address="auto"):
    if ray_address.lower() == "local":
        ray.init()
    else:
        ray.init(address=ray_address)
    
    resources = ray.cluster_resources()
    total_cpus = int(resources.get("CPU", 1))
    ray.shutdown()

    return total_cpus
def main():
    args = buildArgs()
    nucleos = obtenerNucleos(args.ray_address)
    print(f"Actualmente en el cluster hay {nucleos} nucleos")
    print("Iniciando secuencial")
    start = time.perf_counter()
    secuential_process.main(args.input, args.patterns, args.chunk_mb, args.output)
    end = time.perf_counter() 
    secuential_time=end-start
    print(f"Tiempo secuencial: {secuential_time} segundos")
    print("Iniciando distribuido")
    start = time.perf_counter()
    paralel_cluster_process.main(args.input, args.patterns, args.chunk_mb, args.output, args.max_inflight, args.ray_address)
    end = time.perf_counter() 
    distribuido_time=end-start
    print(f"Tiempo distribuido: {distribuido_time} segundos")
    print(f"Speedup: {secuential_time / distribuido_time}")
    
    
if __name__ == "__main__":
    main()