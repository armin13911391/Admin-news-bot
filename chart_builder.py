import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def render_stats_image(report, out_path):
    hours = report["hours"]
    values = report["hourly"]
    now = report["now"]
    labels = [f"{hour:02d}" for hour in hours]
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    fig, axes = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={"height_ratios": [1, 2.2]})
    fig.patch.set_facecolor("#0f172a")
    for ax in axes:
        ax.set_facecolor("#111827")

    axes[0].axis("off")
    title = str(report["channel_id"])
    clock = now.strftime("%H:%M")
    axes[0].text(0.02, 0.82, title, color="#f8fafc", fontsize=20, fontweight="bold", transform=axes[0].transAxes)
    axes[0].text(
        0.02,
        0.52,
        f"00:00  →  {clock}",
        color="#93c5fd",
        fontsize=13,
        transform=axes[0].transAxes,
    )
    cards = [
        ("Today", report["users_today"]),
        ("7 days", report["users_7"]),
        ("30 days", report["users_30"]),
        ("Members", report["members"]),
        ("Posts", report["messages_today"]),
    ]
    for index, (label, value) in enumerate(cards):
        x = 0.02 + index * 0.195
        axes[0].text(x, 0.22, label, color="#94a3b8", fontsize=9, transform=axes[0].transAxes)
        axes[0].text(x, 0.02, str(value), color="#fbbf24", fontsize=16, fontweight="bold", transform=axes[0].transAxes)

    bars = axes[1].bar(labels, values, color="#38bdf8", width=0.72)
    axes[1].set_title("Messages per hour", color="#e2e8f0", fontsize=13, pad=10)
    axes[1].tick_params(colors="#cbd5e1")
    axes[1].set_xlabel("Hour", color="#94a3b8")
    axes[1].set_ylabel("Messages", color="#94a3b8")
    for spine in axes[1].spines.values():
        spine.set_color("#334155")
    axes[1].grid(axis="y", color="#1e293b", linestyle="--", alpha=0.7)
    if values:
        ymax = max(values) if max(values) > 0 else 1
        axes[1].set_ylim(0, ymax * 1.25)
    for bar, value in zip(bars, values):
        if value:
            axes[1].text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.05,
                str(value),
                ha="center",
                va="bottom",
                color="#e2e8f0",
                fontsize=8,
            )

    fig.tight_layout()
    fig.savefig(out_path, dpi=140, facecolor=fig.get_facecolor())
    plt.close(fig)
    return out_path
