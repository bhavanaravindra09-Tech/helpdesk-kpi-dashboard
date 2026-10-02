"""Analyze the synthetic help-desk ticket dataset and save KPI charts.

Reads tickets.csv, computes support KPIs, saves PNG charts into ./charts/,
and prints the key findings to the console.

Charts:
    1. tickets_per_week.png            — ticket volume by week
    2. avg_resolution_hours_by_category.png — mean time to resolve per category
    3. sla_compliance_by_priority.png  — % resolved within 48h, by priority
    4. satisfaction_distribution.png   — count of 1–5 star ratings
    5. avg_first_response_by_priority.png — mean first-response minutes by priority
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless: write PNGs without a display
import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).parent
CHARTS = HERE / "charts"
CHARTS.mkdir(exist_ok=True)

SLA_HOURS = 48
PRIORITY_ORDER = ["Low", "Medium", "High", "Critical"]

try:
    plt.style.use("seaborn-v0_8-whitegrid")
except OSError:
    plt.style.use("default")


def save_bar(series, title, xlabel, ylabel, filename, color="#1f4e79", horizontal=False):
    fig, ax = plt.subplots(figsize=(9, 5))
    if horizontal:
        ax.barh(series.index, series.values, color=color)
        ax.set_xlabel(xlabel)
    else:
        ax.bar(series.index.astype(str), series.values, color=color)
        ax.set_ylabel(ylabel)
        plt.xticks(rotation=30, ha="right")
    ax.set_title(title, fontsize=13, fontweight="bold")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    fig.savefig(CHARTS / filename, dpi=150)
    plt.close(fig)


def main() -> None:
    df = pd.read_csv(
        HERE / "tickets.csv", parse_dates=["created_date", "resolved_date"]
    )
    df["satisfaction"] = pd.to_numeric(df["satisfaction"], errors="coerce")
    df["resolution_hours"] = (
        df["resolved_date"] - df["created_date"]
    ).dt.total_seconds() / 3600

    resolved = df.dropna(subset=["resolved_date"]).copy()
    resolved["sla_met"] = resolved["resolution_hours"] <= SLA_HOURS

    # 1. Ticket volume per week
    weekly = df.set_index("created_date").resample("W").size()
    weekly.index = weekly.index.strftime("%b %d")
    save_bar(weekly, "Tickets Opened per Week", "Week", "Tickets", "tickets_per_week.png")

    # 2. Average resolution time by category
    avg_res = resolved.groupby("category")["resolution_hours"].mean().sort_values()
    save_bar(
        avg_res,
        "Average Resolution Time by Category (hours)",
        "Hours",
        "",
        "avg_resolution_hours_by_category.png",
        horizontal=True,
    )

    # 3. SLA compliance (% resolved within 48h) by priority
    sla = (
        resolved.groupby("priority")["sla_met"]
        .mean()
        .mul(100)
        .reindex(PRIORITY_ORDER)
    )
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(sla.index, sla.values, color="#2e7d32")
    ax.axhline(90, color="#c00000", linestyle="--", label="90% target")
    ax.set_ylim(0, 105)
    ax.set_ylabel("% within 48h")
    ax.set_title("SLA Compliance by Priority (% resolved within 48h)",
                 fontsize=13, fontweight="bold")
    for bar, val in zip(bars, sla.values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 1, f"{val:.1f}%",
                ha="center", fontsize=10)
    ax.legend()
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    fig.savefig(CHARTS / "sla_compliance_by_priority.png", dpi=150)
    plt.close(fig)

    # 4. Satisfaction distribution
    sat = df["satisfaction"].value_counts().sort_index()
    save_bar(sat, "User Satisfaction Ratings (1–5)", "Rating",
             "Tickets", "satisfaction_distribution.png", color="#ed7d31")

    # 5. Average first response by priority
    fr = df.groupby("priority")["first_response_minutes"].mean().reindex(PRIORITY_ORDER)
    save_bar(fr, "Average First-Response Time by Priority (minutes)", "Priority",
             "Minutes", "avg_first_response_by_priority.png", color="#7030a0")

    # ---- Key findings (computed from the data, not invented) ----
    total = len(df)
    resolved_n = len(resolved)
    sla_overall = resolved["sla_met"].mean() * 100
    slowest_cat = avg_res.idxmax()
    slowest_cat_h = avg_res.max()
    fastest_cat = avg_res.idxmin()
    slowest_fr = fr.idxmax()
    avg_sat = df["satisfaction"].mean()
    sat_4_5 = (df["satisfaction"] >= 4).mean() * 100
    busiest_week = weekly.idxmax()
    critical_sla = sla.loc["Critical"]

    print("KEY FINDINGS")
    print(f"1. Volume & closure: {total} tickets over 12 weeks; "
          f"{resolved_n} resolved ({resolved_n / total * 100:.1f}%), "
          f"busiest week starting {busiest_week}.")
    print(f"2. SLA compliance: {sla_overall:.1f}% of resolved tickets closed within "
          f"{SLA_HOURS}h; Critical-priority SLA compliance is {critical_sla:.1f}%.")
    print(f"3. Slowest category: '{slowest_cat}' averages {slowest_cat_h:.1f}h to "
          f"resolve vs '{fastest_cat}' at {avg_res.min():.1f}h — the main "
          f"bottleneck for SLA performance.")
    print(f"4. First response: '{slowest_fr}' priority averages {fr.max():.1f} min "
          f"to first response; Critical averages {fr.loc['Critical']:.1f} min.")
    print(f"5. Satisfaction: average rating {avg_sat:.2f}/5, with "
          f"{sat_4_5:.1f}% of rated tickets at 4–5 stars.")
    print(f"\nCharts saved to {CHARTS}")


if __name__ == "__main__":
    main()
