def generate_report(cpu_info, results, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("==== REPORTE DE RENDIMIENTO ====\n\n")

        f.write(">> CPU DETECTADA:\n")
        f.write(f"Modelo: {cpu_info['cpu_model']}\n")
        f.write(f"Arquitectura: {cpu_info['cpu_arch']}\n")
        f.write(f"Cores: {cpu_info['cpu_cores']}\n")
        f.write(f"Threads: {cpu_info['cpu_threads']}\n\n")
        f.write(f"RAM Total: {cpu_info['ram_total_gb']} GB\n")
        f.write(f"RAM Disponible: {cpu_info['ram_available_gb']} GB\n\n")
        f.buffer.write(f"FLOPS Teóricos CPU: {cpu_info['cpu_flops_theoretical']:.2e}\n\n".encode("utf-8"))
        f.buffer.write(f"FLOPS Reales CPU: {results['cpu']['real']:.2e}\n\n".encode("utf-8"))
        f.buffer.write(f"Eficiencia CPU: {(results['cpu']['real'] / cpu_info['cpu_flops_theoretical']) * 100:.2f}%\n\n".encode("utf-8"))
        f.buffer.write(f"GPU Detectada: {'SI' if cpu_info['gpu_available'] else 'NO'}\n\n".encode("utf-8"))
    

        f.write(">> RESULTADOS:\n")
        for k, v in results.items():
            eficiencia = (v["real"] / v["teorico"]) * 100
            f.write(f"{k}:\n")
            f.write(f"  FLOPS Teórico: {v['teorico']:.2e}\n")
            f.write(f"  FLOPS Real: {v['real']:.2e}\n")
            f.write(f"  Eficiencia: {eficiencia:.2f}%\n\n")

        f.write(">> GPU:\n")
        f.write("No detectada (versión actual)\n")

        f.write("\n==== FIN DEL REPORTE ====\n")
