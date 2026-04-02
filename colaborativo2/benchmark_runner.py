import argparse
import os
from pathlib import Path

import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

from benchmark_models import BenchmarkRun
from cpu_integration import cpu_calculation
from gpu_integration import gpu_calculation, gpu_support_status
from resource_monitor import ResourceMonitor


def get_args():
    parser = argparse.ArgumentParser(description="Benchmark CPU y GPU usando el archivo completo.")
    parser.add_argument("--file", required=True, type=str, help="Archivo FASTA fuente.")
    parser.add_argument("--converter-path", required=True, type=str, help="Ejecutable C para convertir FASTA a binario.")
    parser.add_argument("--processors", type=int, default=os.cpu_count() or 1, help="Procesos para la version CPU.")
    parser.add_argument("--repeats", type=int, default=1, help="Repeticiones por backend sobre el archivo completo.")
    parser.add_argument("--output-dir", type=str, default="benchmark_artifacts", help="Directorio de salida.")
    parser.add_argument("--skip-cpu", action="store_true", help="Omite benchmarks CPU.")
    parser.add_argument("--skip-gpu", action="store_true", help="Omite benchmarks GPU.")
    return parser.parse_args()


def run_single_benchmark(
    backend: str,
    input_path: Path,
    input_bases: int,
    processors: int,
    repeat: int,
    converter_path: Path,
) -> BenchmarkRun:
    monitor = ResourceMonitor(enable_gpu=backend == "GPU")
    monitor.start()
    try:
        if backend == "CPU":
            analysis = cpu_calculation(str(input_path), processors)
        else:
            analysis = gpu_calculation(str(converter_path), str(input_path))
    finally:
        resources = monitor.stop()

    effective_input_bases = input_bases
    if effective_input_bases <= 0:
        effective_input_bases = sum(analysis.result.values())

    return BenchmarkRun(
        backend=backend,
        input_path=input_path,
        input_bases=effective_input_bases,
        processors=processors if backend == "CPU" else None,
        repeat=repeat,
        analysis=analysis,
        resources=resources,
    )


def _save_backend_barplot(dataframe: pd.DataFrame, metric: str, title: str, ylabel: str, output_path: Path) -> None:
    plt.figure(figsize=(9, 6))
    sns.barplot(data=dataframe, x="backend", y=metric, hue="backend", errorbar="sd", legend=False)
    sns.stripplot(data=dataframe, x="backend", y=metric, hue="backend", dodge=False, alpha=0.55, size=7, legend=False)
    plt.title(title)
    plt.xlabel("Backend")
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def create_plots(dataframe: pd.DataFrame, output_dir: Path) -> None:
    plots_dir = output_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    sns.set_theme(style="whitegrid", palette="deep")

    _save_backend_barplot(
        dataframe=dataframe,
        metric="time_seconds",
        title="Comparacion de tiempo total de ejecucion",
        ylabel="Tiempo total (s)",
        output_path=plots_dir / "comparacion_tiempos.png",
    )

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    sns.barplot(data=dataframe, x="backend", y="avg_cpu_percent", hue="backend", errorbar="sd", legend=False, ax=axes[0, 0])
    axes[0, 0].set_title("Uso promedio de CPU")
    axes[0, 0].set_xlabel("Backend")
    axes[0, 0].set_ylabel("CPU (%)")

    sns.barplot(data=dataframe, x="backend", y="peak_memory_mb", hue="backend", errorbar="sd", legend=False, ax=axes[0, 1])
    axes[0, 1].set_title("Pico de memoria RAM")
    axes[0, 1].set_xlabel("Backend")
    axes[0, 1].set_ylabel("Memoria (MB)")

    gpu_frame = dataframe.dropna(subset=["avg_gpu_util_percent", "peak_gpu_memory_mb"])
    if not gpu_frame.empty:
        sns.barplot(data=gpu_frame, x="backend", y="avg_gpu_util_percent", hue="backend", errorbar="sd", legend=False, ax=axes[1, 0])
        sns.barplot(data=gpu_frame, x="backend", y="peak_gpu_memory_mb", hue="backend", errorbar="sd", legend=False, ax=axes[1, 1])
    axes[1, 0].set_title("Uso promedio de GPU")
    axes[1, 0].set_xlabel("Backend")
    axes[1, 0].set_ylabel("GPU (%)")

    axes[1, 1].set_title("Pico de memoria GPU")
    axes[1, 1].set_xlabel("Backend")
    axes[1, 1].set_ylabel("Memoria GPU (MB)")

    fig.tight_layout()
    fig.savefig(plots_dir / "uso_recursos.png", dpi=200)
    plt.close(fig)

    _save_backend_barplot(
        dataframe=dataframe,
        metric="invalids_per_second",
        title="Velocidad de identificacion de errores por segundo",
        ylabel="Errores por segundo",
        output_path=plots_dir / "errores_por_segundo.png",
    )

    _save_backend_barplot(
        dataframe=dataframe,
        metric="bases_per_second",
        title="Rendimiento global sobre el archivo completo",
        ylabel="Bases procesadas por segundo",
        output_path=plots_dir / "rendimiento_global.png",
    )


def write_summary(dataframe: pd.DataFrame, output_dir: Path) -> None:
    summary_path = output_dir / "summary.md"
    grouped = dataframe.groupby("backend", dropna=False).agg(
        repeticiones=("repeat", "count"),
        tiempo_promedio_s=("time_seconds", "mean"),
        tiempo_min_s=("time_seconds", "min"),
        tiempo_max_s=("time_seconds", "max"),
        max_memoria_mb=("peak_memory_mb", "max"),
        cpu_promedio_pct=("avg_cpu_percent", "mean"),
        gpu_promedio_pct=("avg_gpu_util_percent", "mean"),
        errores_por_segundo=("invalids_per_second", "mean"),
        throughput_bases_s=("bases_per_second", "mean"),
    )

    lines = [
        "# Resumen de benchmarks",
        "",
        "Archivo analizado completo en todas las ejecuciones.",
        "",
        "## Ejecuciones",
        "",
        "```text",
        dataframe.to_string(index=False),
        "```",
        "",
        "## Promedios por backend",
        "",
        "```text",
        grouped.reset_index().to_string(index=False),
        "```",
    ]
    summary_path.write_text("\n".join(lines), encoding="utf-8")


def run_benchmarks(
    file_path: str,
    converter_path: str,
    processors: int,
    repeats: int,
    output_dir: str = "benchmark_artifacts",
    skip_cpu: bool = False,
    skip_gpu: bool = False,
) -> pd.DataFrame:
    source_path = Path(file_path).resolve()
    converter = Path(converter_path).resolve()
    artifacts_dir = Path(output_dir).resolve()
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    selected_backends: list[str] = []
    if not skip_cpu:
        selected_backends.append("CPU")
    if not skip_gpu:
        selected_backends.append("GPU")
    if not selected_backends:
        raise ValueError("No hay backends habilitados. Usa sin --skip-* o habilita al menos uno.")

    if "GPU" in selected_backends:
        available, message = gpu_support_status()
        if not available:
            raise RuntimeError(f"No se puede ejecutar GPU: {message}")

    runs: list[BenchmarkRun] = []
    print(f"Archivo completo seleccionado: {source_path.name}", flush=True)
    for backend in selected_backends:
        for repeat in range(1, repeats + 1):
            print(f"Ejecutando {backend}, repeticion {repeat}/{repeats}", flush=True)
            runs.append(
                run_single_benchmark(
                    backend=backend,
                    input_path=source_path,
                    input_bases=0,
                    processors=processors,
                    repeat=repeat,
                    converter_path=converter,
                )
            )

    dataframe = pd.DataFrame(run.to_record() for run in runs)
    csv_path = artifacts_dir / "benchmark_results.csv"
    dataframe.to_csv(csv_path, index=False)
    write_summary(dataframe, artifacts_dir)
    create_plots(dataframe, artifacts_dir)

    print(f"Resultados guardados en {csv_path}", flush=True)
    print(f"Graficas guardadas en {artifacts_dir / 'plots'}", flush=True)
    return dataframe


def main():
    args = get_args()
    run_benchmarks(
        file_path=args.file,
        converter_path=args.converter_path,
        processors=args.processors,
        repeats=args.repeats,
        output_dir=args.output_dir,
        skip_cpu=args.skip_cpu,
        skip_gpu=args.skip_gpu,
    )


if __name__ == "__main__":
    main()
