from src.hardware_info import get_hardware_info
from src.benchmark import run_benchmark
from src.visualization import generate_report_and_plot

def main():
    print("\n=== BENCHMARK DE RENDIMIENTO ===")
    nombre_usuario = input("¿Quién está ejecutando el benchmark? Ingresa tu nombre: ").strip()
    
    if not nombre_usuario:
        nombre_usuario = "Usuario Desconocido"
    
    print("\n=== ANALIZANDO HARDWARE ===")
    hw_info = get_hardware_info()
    print(hw_info)

    print("\n=== EJECUTANDO BENCHMARK REAL ===")
    flops_real = run_benchmark()
    print(f"FLOPS reales medidos: {flops_real:,.2f}")

    print("\n=== GENERANDO REPORTE Y GRÁFICO ===")
    generate_report_and_plot(hw_info, flops_real, nombre_usuario)

    print("\n✔ Proceso terminado. Revisa la carpeta /report\n")

if __name__ == "__main__":
    main()
