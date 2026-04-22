def generate_report(cpu_info, results, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("==== REPORTE DE RENDIMIENTO ====\n\n")

        f.write(">> CPU DETECTADA:\n")
        f.write(f"Modelo: {cpu_info['modelo']}\n")
        f.write(f"Arquitectura: {cpu_info['arquitectura']}\n")
        f.write(f"Cores: {cpu_info['cores']}\n")
        f.write(f"Threads: {cpu_info['threads']}\n\n")

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
