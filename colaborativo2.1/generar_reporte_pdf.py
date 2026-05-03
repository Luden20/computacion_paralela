"""
generar_reporte_pdf.py
─────────────────────
Lee los últimos 4 registros de report/historico.json y genera
un reporte comparativo en PDF (report/reporte_comparativo.pdf).

Uso:
    python generar_reporte_pdf.py
    python generar_reporte_pdf.py --historico ruta/al/historico.json
"""

import json
import os
import sys
import argparse
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image, PageBreak,
)


# ── Rutas por defecto ──────────────────────────────────────────────────────────
HISTORICO_DEFAULT = "report/historico.json"
SALIDA_PDF        = "report/reporte_comparativo.pdf"
GRAFICO_TEMP      = "report/temp_grafico.png"


# ── Colores de marca ───────────────────────────────────────────────────────────
AZUL_OSCURO  = colors.HexColor("#1B3A6B")
AZUL_CLARO   = colors.HexColor("#4C72B0")
VERDE        = colors.HexColor("#2E8B57")
GRIS_CLARO   = colors.HexColor("#F0F4FA")
GRIS_MEDIO   = colors.HexColor("#D0D8E8")
BLANCO       = colors.white


def cargar_ultimos(path: str, n: int = 4) -> list:
    """Carga los últimos N registros del JSON histórico."""
    if not os.path.exists(path):
        sys.exit(f"[ERROR] No se encontró el archivo: {path}")
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            sys.exit(f"[ERROR] JSON inválido: {e}")
    if not data:
        sys.exit("[ERROR] El historial está vacío.")
    return data[-4:]  # últimos N


def fmt_flops(valor: float) -> str:
    """Formatea un número de FLOPS en unidades legibles (GFLOPS / TFLOPS)."""
    if valor >= 1e12:
        return f"{valor / 1e12:.2f} TFLOPS"
    return f"{valor / 1e9:.2f} GFLOPS"


def generar_grafico(registros: list, ruta_salida: str) -> None:
    """Genera gráfico de barras comparativo (teórico vs real) para todos los registros."""
    usuarios   = [r["usuario"] for r in registros]
    teoricos   = [r["flops_teoricos"] / 1e9 for r in registros]   # en GFLOPS
    reales     = [r["flops_reales"]   / 1e9 for r in registros]

    x      = range(len(usuarios))
    ancho  = 0.35
    fig, ax = plt.subplots(figsize=(10, 5))

    barras_t = ax.bar([i - ancho/2 for i in x], teoricos, ancho,
                      label="FLOPS Teóricos", color="#4C72B0", zorder=3)
    barras_r = ax.bar([i + ancho/2 for i in x], reales, ancho,
                      label="FLOPS Reales",    color="#2E8B57", zorder=3)

    ax.set_xticks(list(x))
    ax.set_xticklabels(usuarios, fontsize=9)
    ax.set_ylabel("GFLOPS", fontsize=10)
    ax.set_title("Comparativa de Rendimiento — Últimos 4 Registros", fontsize=12, fontweight="bold")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}"))
    ax.legend(fontsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.5, zorder=0)

    # Etiquetas sobre barras
    for b in list(barras_t) + list(barras_r):
        ax.annotate(
            f"{b.get_height():.0f}",
            xy=(b.get_x() + b.get_width() / 2, b.get_height()),
            xytext=(0, 4), textcoords="offset points",
            ha="center", fontsize=7,
        )

    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=150)
    plt.close()


def construir_pdf(registros: list, ruta_pdf: str, ruta_grafico: str) -> None:
    """Construye el PDF con portada, tabla resumen, gráfico y fichas por usuario."""

    doc = SimpleDocTemplate(
        ruta_pdf,
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=2.5*cm,
    )

    styles = getSampleStyleSheet()
    ancho_util = A4[0] - 4*cm   # 595 - 4 cm de márgenes

    # ── Estilos personalizados ────────────────────────────────────────────────
    estilo_titulo = ParagraphStyle(
        "Titulo", parent=styles["Title"],
        fontSize=22, textColor=BLANCO,
        alignment=TA_CENTER, spaceAfter=4,
    )
    estilo_subtitulo = ParagraphStyle(
        "Subtitulo", parent=styles["Normal"],
        fontSize=11, textColor=GRIS_MEDIO,
        alignment=TA_CENTER, spaceAfter=2,
    )
    estilo_h1 = ParagraphStyle(
        "H1", parent=styles["Heading1"],
        fontSize=13, textColor=AZUL_OSCURO,
        spaceBefore=14, spaceAfter=6,
    )
    estilo_h2 = ParagraphStyle(
        "H2", parent=styles["Heading2"],
        fontSize=11, textColor=AZUL_CLARO,
        spaceBefore=8, spaceAfter=4,
    )
    estilo_normal = ParagraphStyle(
        "Normal2", parent=styles["Normal"],
        fontSize=9, leading=14,
    )
    estilo_pie = ParagraphStyle(
        "Pie", parent=styles["Normal"],
        fontSize=7, textColor=colors.grey,
        alignment=TA_CENTER,
    )

    historia = []   # flowables del documento

    # ════════════════════════════════════════════════════════════════════════════
    # PORTADA (banner de color)
    # ════════════════════════════════════════════════════════════════════════════
    banner_data = [[Paragraph(
        "<b>REPORTE COMPARATIVO DE RENDIMIENTO</b>", estilo_titulo
    )]]
    banner = Table(banner_data, colWidths=[ancho_util])
    banner.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), AZUL_OSCURO),
        ("ROUNDEDCORNERS", [6]),
        ("TOPPADDING",   (0, 0), (-1, -1), 18),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 18),
    ]))
    historia.append(banner)
    historia.append(Spacer(1, 0.3*cm))
    historia.append(Paragraph(
        f"Últimos 4 registros del historial de ejecución  ·  "
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        estilo_subtitulo,
    ))
    historia.append(Spacer(1, 0.8*cm))

    # ════════════════════════════════════════════════════════════════════════════
    # TABLA RESUMEN
    # ════════════════════════════════════════════════════════════════════════════
    historia.append(Paragraph("Resumen General", estilo_h1))
    historia.append(HRFlowable(width="100%", thickness=1, color=AZUL_CLARO))
    historia.append(Spacer(1, 0.3*cm))

    encabezado = [
        Paragraph("<b>Usuario</b>",         estilo_normal),
        Paragraph("<b>Fecha</b>",           estilo_normal),
        Paragraph("<b>CPU</b>",             estilo_normal),
        Paragraph("<b>FLOPS Teóricos</b>",  estilo_normal),
        Paragraph("<b>FLOPS Reales</b>",    estilo_normal),
        Paragraph("<b>Eficiencia</b>",      estilo_normal),
    ]
    filas = [encabezado]

    for r in registros:
        hw = r.get("hardware", {})
        cpu_corto = hw.get("cpu_model", "—")
        # Acortar modelo largo
        if len(cpu_corto) > 22:
            cpu_corto = cpu_corto[:20] + "…"
        filas.append([
            Paragraph(r["usuario"],              estilo_normal),
            Paragraph(r["fecha"][:10],           estilo_normal),
            Paragraph(cpu_corto,                 estilo_normal),
            Paragraph(fmt_flops(r["flops_teoricos"]), estilo_normal),
            Paragraph(fmt_flops(r["flops_reales"]),   estilo_normal),
            Paragraph(f"{r['eficiencia_pct']:.2f}%",  estilo_normal),
        ])

    col_anchos = [
        ancho_util * 0.18,
        ancho_util * 0.13,
        ancho_util * 0.22,
        ancho_util * 0.16,
        ancho_util * 0.16,
        ancho_util * 0.15,
    ]
    tabla_res = Table(filas, colWidths=col_anchos, repeatRows=1)
    tabla_res.setStyle(TableStyle([
        # Encabezado
        ("BACKGROUND",    (0, 0), (-1, 0),  AZUL_OSCURO),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  BLANCO),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        # Filas alternas
        *[("BACKGROUND", (0, i), (-1, i), GRIS_CLARO)
          for i in range(2, len(filas), 2)],
        # Bordes
        ("GRID",          (0, 0), (-1, -1), 0.4, GRIS_MEDIO),
        ("ROWBACKGROUND", (0, 1), (-1, -1), BLANCO),
        # Padding
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    historia.append(tabla_res)
    historia.append(Spacer(1, 0.8*cm))

    # ════════════════════════════════════════════════════════════════════════════
    # GRÁFICO COMPARATIVO
    # ════════════════════════════════════════════════════════════════════════════
    historia.append(Paragraph("Gráfico Comparativo de FLOPS", estilo_h1))
    historia.append(HRFlowable(width="100%", thickness=1, color=AZUL_CLARO))
    historia.append(Spacer(1, 0.3*cm))

    img_ancho = ancho_util
    img_alto  = img_ancho * 0.5
    historia.append(Image(ruta_grafico, width=img_ancho, height=img_alto))
    historia.append(Spacer(1, 0.3*cm))
    historia.append(Paragraph(
        "Nota: FLOPS = Operaciones de Punto Flotante por Segundo. "
        "La barra azul muestra la capacidad teórica máxima de la CPU "
        "y la verde el rendimiento medido en el benchmark.",
        estilo_pie,
    ))

    historia.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════════
    # FICHAS INDIVIDUALES
    # ════════════════════════════════════════════════════════════════════════════
    historia.append(Paragraph("Fichas Detalladas por Participante", estilo_h1))
    historia.append(HRFlowable(width="100%", thickness=1, color=AZUL_CLARO))

    for idx, r in enumerate(registros, 1):
        hw = r.get("hardware", {})
        eficiencia = r.get("eficiencia_pct", 0)

        historia.append(Spacer(1, 0.5*cm))

        # Encabezado de ficha
        titulo_ficha = [[Paragraph(
            f"<b>#{idx} — {r['usuario']}</b>  "
            f"<font size='9' color='#AACCFF'>({r['fecha']})</font>",
            ParagraphStyle("FichaH", parent=estilo_normal,
                           textColor=BLANCO, fontSize=10),
        )]]
        tabla_titulo = Table(titulo_ficha, colWidths=[ancho_util])
        tabla_titulo.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), AZUL_CLARO),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ]))
        historia.append(tabla_titulo)

        # Columna izquierda: hardware  |  Columna derecha: resultados
        col_hw = [
            [Paragraph("<b>Especificaciones de Hardware</b>", estilo_h2)],
            [Paragraph(f"Modelo CPU : {hw.get('cpu_model', '—')}",      estilo_normal)],
            [Paragraph(f"Núcleos    : {hw.get('cpu_cores', '—')}",      estilo_normal)],
            [Paragraph(f"Hilos      : {hw.get('cpu_threads', '—')}",    estilo_normal)],
            [Paragraph(f"Frecuencia : {hw.get('cpu_freq_ghz', '—')} GHz", estilo_normal)],
            [Paragraph(f"RAM Total  : {hw.get('ram_total_gb', '—')} GB", estilo_normal)],
            [Paragraph(f"GPU        : {hw.get('gpu_model', 'No detectada')}", estilo_normal)],
        ]
        col_res = [
            [Paragraph("<b>Resultados del Benchmark</b>", estilo_h2)],
            [Paragraph(f"FLOPS Teóricos : {fmt_flops(r['flops_teoricos'])}", estilo_normal)],
            [Paragraph(f"FLOPS Reales   : {fmt_flops(r['flops_reales'])}", estilo_normal)],
            [Paragraph(f"Eficiencia CPU : {eficiencia:.2f}%", estilo_normal)],
            [Paragraph(
                "Rendimiento ALTO" if eficiencia >= 55 else
                "Rendimiento MEDIO" if eficiencia >= 40 else
                "Rendimiento BAJO",
                ParagraphStyle(
                    "Badge", parent=estilo_normal,
                    textColor=VERDE if eficiencia >= 55 else
                              AZUL_CLARO if eficiencia >= 40 else
                              colors.red,
                    fontName="Helvetica-Bold",
                )
            )],
        ]

        mitad = ancho_util / 2 - 0.1*cm
        tabla_hw  = Table(col_hw,  colWidths=[mitad])
        tabla_res2 = Table(col_res, colWidths=[mitad])

        for t in (tabla_hw, tabla_res2):
            t.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), GRIS_CLARO),
                ("TOPPADDING",    (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING",   (0, 0), (-1, -1), 10),
                ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ]))

        tabla_dos_col = Table(
            [[tabla_hw, tabla_res2]],
            colWidths=[mitad, mitad],
        )
        tabla_dos_col.setStyle(TableStyle([
            ("VALIGN",      (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ]))
        historia.append(tabla_dos_col)

    # ════════════════════════════════════════════════════════════════════════════
    # PIE DE PÁGINA
    # ════════════════════════════════════════════════════════════════════════════
    historia.append(Spacer(1, 1*cm))
    historia.append(HRFlowable(width="100%", thickness=0.5, color=GRIS_MEDIO))
    historia.append(Spacer(1, 0.2*cm))
    historia.append(Paragraph(
        "Reporte generado automáticamente por el sistema de medición de FLOPS  ·  "
        f"{datetime.now().strftime('%d/%m/%Y %H:%M')}",
        estilo_pie,
    ))

    doc.build(historia)


# ── Punto de entrada ──────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Genera un PDF con los últimos 4 registros del historial de FLOPS."
    )
    parser.add_argument(
        "--historico", default=HISTORICO_DEFAULT,
        help=f"Ruta al JSON histórico (por defecto: {HISTORICO_DEFAULT})"
    )
    args = parser.parse_args()

    print(f"\n[1/4] Cargando historial: {args.historico}")
    registros = cargar_ultimos(args.historico, n=4)
    print(f"      {len(registros)} registro(s) cargado(s).")

    os.makedirs("report", exist_ok=True)

    print("[2/4] Generando gráfico comparativo...")
    generar_grafico(registros, GRAFICO_TEMP)

    print("[3/4] Construyendo PDF...")
    construir_pdf(registros, SALIDA_PDF, GRAFICO_TEMP)

    # Limpiar imagen temporal
    if os.path.exists(GRAFICO_TEMP):
        os.remove(GRAFICO_TEMP)

    print(f"[4/4] ✔ PDF generado: {SALIDA_PDF}\n")


if __name__ == "__main__":
    main()