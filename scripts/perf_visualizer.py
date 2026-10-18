#!/usr/bin/env python3
"""
Performance visualization script for the 5-stage RV32I pipelined processor.
Reads benchmark metrics from a CSV file and generates a publication-quality chart.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parent.parent
    default_csv = repo_root / "results" / "pipeline_stats.csv"
    default_img = repo_root / "results" / "performance_graph.png"

    parser = argparse.ArgumentParser(
        description="Generate performance summary charts from pipeline execution statistics."
    )
    parser.add_argument(
        "-i", "--input",
        type=Path,
        default=default_csv,
        help="Path to pipeline_stats.csv (default: %(default)s)"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=default_img,
        help="Path for output PNG image (default: %(default)s)"
    )
    return parser.parse_args()


def load_pipeline_metrics(csv_path: Path) -> dict[str, float]:
    if not csv_path.is_file():
        raise FileNotFoundError(f"Statistics file not found: {csv_path}")

    df = pd.read_csv(csv_path)

    # Support either key-value pairs (Metric, Value) or single-row tabular data
    if {"Metric", "Value"}.issubset(df.columns):
        raw_metrics = dict(zip(df["Metric"].astype(str).str.strip(), df["Value"]))
    elif not df.empty:
        raw_metrics = {str(k).strip(): v for k, v in df.iloc[0].items()}
    else:
        raise ValueError(f"Input CSV is empty: {csv_path}")

    def lookup(primary: str, *aliases: str) -> float:
        for key in (primary, *aliases):
            if key in raw_metrics:
                try:
                    return float(raw_metrics[key])
                except (ValueError, TypeError) as exc:
                    raise ValueError(f"Invalid numeric value for '{key}': {raw_metrics[key]}") from exc
        raise KeyError(f"Metric '{primary}' not found in CSV (checked aliases: {aliases})")

    total_cycles = lookup("Total Cycles", "Total_Cycles", "Cycles")
    instructions = lookup("Executed Instructions", "Executed_Instructions", "Instructions")
    stalls = lookup("Stalls", "Stall_Count", "Stall Cycles")
    flushes = lookup("Flushes", "Flush_Count", "Flush Cycles")

    # Compute IPC / CPI if not explicitly present
    try:
        ipc = lookup("IPC")
    except KeyError:
        ipc = instructions / total_cycles if total_cycles > 0 else 0.0

    try:
        cpi = lookup("CPI")
    except KeyError:
        cpi = total_cycles / instructions if instructions > 0 else 0.0

    return {
        "Total Cycles": total_cycles,
        "Executed Instructions": instructions,
        "Stalls": stalls,
        "Flushes": flushes,
        "IPC": ipc,
        "CPI": cpi,
    }


def render_performance_chart(metrics: dict[str, float], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8.5, 5.2), dpi=300)

    # Slate theme
    fig.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#1e293b")

    labels = ["Total Cycles", "Executed\nInstructions", "Load-Use\nStalls", "Branch\nFlushes"]
    values = [
        int(metrics["Total Cycles"]),
        int(metrics["Executed Instructions"]),
        int(metrics["Stalls"]),
        int(metrics["Flushes"]),
    ]
    palette = ["#38bdf8", "#34d399", "#fbbf24", "#f87171"]

    bars = ax.bar(
        labels,
        values,
        color=palette,
        width=0.52,
        edgecolor="#334155",
        linewidth=1.2,
        zorder=3
    )

    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f"{int(height):,}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 6),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=10.5,
            fontweight="bold",
            color="#f8fafc",
        )

    ax.set_title(
        "RV32I 5-Stage Pipelined Core — Benchmark Execution Profile",
        fontsize=13,
        fontweight="bold",
        color="#f8fafc",
        pad=16,
    )
    ax.set_ylabel("Cycle / Instruction Count", fontsize=10.5, color="#94a3b8")
    ax.tick_params(axis="x", colors="#e2e8f0", labelsize=10)
    ax.tick_params(axis="y", colors="#94a3b8", labelsize=9.5)
    ax.grid(axis="y", linestyle="--", alpha=0.2, color="#94a3b8", zorder=0)
    ax.set_ylim(0, max(values) * 1.22)

    for spine in ax.spines.values():
        spine.set_color("#334155")

    # Metric annotations
    total = metrics["Total Cycles"]
    stall_ratio = (metrics["Stalls"] / total) * 100 if total > 0 else 0.0
    flush_ratio = (metrics["Flushes"] / total) * 100 if total > 0 else 0.0

    summary_text = (
        f"IPC: {metrics['IPC']:.3f}\n"
        f"CPI: {metrics['CPI']:.3f}\n"
        f"Stall Overhead: {stall_ratio:.1f}%\n"
        f"Flush Overhead: {flush_ratio:.1f}%"
    )
    ax.text(
        0.96,
        0.94,
        summary_text,
        transform=ax.transAxes,
        fontsize=9,
        fontfamily="monospace",
        color="#e2e8f0",
        va="top",
        ha="right",
        bbox=dict(
            boxstyle="round,pad=0.6",
            facecolor="#0f172a",
            edgecolor="#475569",
            alpha=0.92,
            linewidth=1.0,
        ),
        zorder=4,
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    print(f"Chart saved to {output_path}")


def main() -> int:
    args = parse_args()
    try:
        metrics = load_pipeline_metrics(args.input)
        render_performance_chart(metrics, args.output)
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
