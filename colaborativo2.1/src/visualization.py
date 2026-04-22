import matplotlib.pyplot as plt
import os

def generate_report_and_plot(hw_info, flops_real):
    os.makedirs("report", exist_ok=True)

    cpu_theoretical = hw_info["cpu_flops_theoretical"]

    # ------- PLOT -------
    plt.figure(figsize=(8,5))
    plt.bar(["Teórico CPU", "Real"], [cpu_theoretical, flops_real])
    plt.ylabel("FLOPS")
    plt.title("Desempeño de Cómputo (CPU)")
    plt.savefig("report/resultados.png")
    plt.close()

    # ------- REPORTE -------
    with open("report/reporte.txt", "w", encoding="utf-8") as f:
        f.write("===== REPORTE DE RENDIMIENTO =====\n\n")
        f.write(f"CPU detectada: {hw_info['cpu_model']}\n")
        f.write(f"Núcleos: {hw_info['cpu_cores']} | Hilos: {hw_info['cpu_threads']}\n")
        f.write(f"Frecuencia máxima: {hw_info['cpu_freq_ghz']} GHz\n\n")
        
        f.write("--- GPU ---\n")
        f.write("GPU detectada: SI\n" if hw_info["gpu_available"] else "GPU detectada: NO\n")
        
        f.write("\n--- FLOPS ---\n")
        f.write(f"FLOPS teóricos CPU: {cpu_theoretical:,.2f}\n")
        f.write(f"FLOPS reales CPU: {flops_real:,.2f}\n")
