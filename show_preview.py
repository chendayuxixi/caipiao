# -*- coding: utf-8 -*-
"""
生成预览截图
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patheffects as pe
from datetime import datetime

# ── 专业量化配色方案 ──────────────────────────────────────────
COLORS = {
    "bg":           "#0A0E14",
    "card":         "#131A24",
    "grid":         "#1E2A38",
    "border":       "#2A3A4E",
    "border_light": "#3A4F6A",
    "text":         "#E6EDF3",
    "text_secondary": "#B0BAC5",
    "text_dim":     "#768390",
    "text_muted":   "#545D68",
    "red":          "#FF4757",
    "red_bright":   "#FF6B81",
    "red_glow":     "#FF475740",
    "green":        "#2ED573",
    "green_bright":  "#7BED9F",
    "green_glow":   "#2ED57340",
    "blue":         "#3498DB",
    "blue_bright":  "#5DADE2",
    "blue_glow":    "#3498DB30",
    "orange":       "#F39C12",
    "orange_bright": "#F1C40F",
    "orange_glow":  "#F39C1230",
    "yellow_bright": "#F4D03F",
    "cyan_bright":  "#48C9B0",
    "cyan_glow":    "#1ABC9C30",
    "shadow":       "#00000040",
}

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

def apply_dark_style(fig, axes):
    fig.patch.set_facecolor(COLORS["bg"])
    for ax in axes:
        ax.set_facecolor(COLORS["card"])
        ax.tick_params(colors=COLORS["text_dim"], labelsize=9, length=4, width=0.8)
        ax.xaxis.label.set_color(COLORS["text_secondary"])
        ax.yaxis.label.set_color(COLORS["text_secondary"])
        ax.title.set_color(COLORS["text"])
        ax.title.set_fontsize(13)
        ax.title.set_fontweight("bold")
        for spine in ax.spines.values():
            spine.set_color(COLORS["border"])
            spine.set_linewidth(0.8)
        ax.grid(True, color=COLORS["grid"], alpha=0.5, linewidth=0.6)
        ax.set_axisbelow(True)
        ax.axhline(y=0, color=COLORS["border_light"], linewidth=1.0, alpha=0.8)


def generate_preview():
    # 生成模拟数据
    morning_times = pd.date_range(start="2026-06-21 09:30", end="2026-06-21 11:30", freq="1min")
    afternoon_times = pd.date_range(start="2026-06-21 13:00", end="2026-06-21 15:00", freq="1min")
    all_times = pd.DatetimeIndex(morning_times.tolist() + afternoon_times.tolist())
    n = len(all_times)
    np.random.seed(42)

    main_flow = np.cumsum(np.random.randn(n) * 1000000)
    small_flow = -main_flow * 0.3 + np.cumsum(np.random.randn(n) * 200000)
    medium_flow = np.cumsum(np.random.randn(n) * 300000)

    df = pd.DataFrame({
        "time": all_times,
        "主力净流入": main_flow,
        "小单净流入": small_flow,
        "中单净流入": medium_flow,
    })

    for col in ["主力净流入", "小单净流入", "中单净流入"]:
        df[f"{col}(万)"] = df[col] / 10000
    df["主力累计(万)"] = df["主力净流入(万)"].cumsum()

    # 创建图表
    fig = plt.figure(figsize=(16, 10), dpi=120)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.2, 1], width_ratios=[3, 1],
                          hspace=0.3, wspace=0.25, left=0.06, right=0.94, top=0.88, bottom=0.08)

    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[1, 0])
    ax_stats = fig.add_subplot(gs[0, 1])
    ax_info = fig.add_subplot(gs[1, 1])

    axes = [ax1, ax2, ax_stats, ax_info]
    apply_dark_style(fig, axes)

    for ax in [ax_stats, ax_info]:
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_linewidth(0.6)

    # 标题
    fig.suptitle("贵州茅台（600519）资金流向分析", fontsize=18, fontweight="bold",
                 color=COLORS["text"], y=0.94)
    fig.text(0.5, 0.90, f"数据时间: 2026-06-21 09:30 - 15:00",
             fontsize=10, color=COLORS["text_dim"], ha='center')

    # 子图1：分时资金净流入
    ax1.set_ylabel("净流入金额（万元）", fontsize=11, color=COLORS["text_secondary"])
    ax1.set_title("分时资金净流入", fontsize=13, fontweight="bold", color=COLORS["text"], loc="left")

    x_min, x_max = df["time"].min(), df["time"].max()
    y_min = min(df["主力净流入(万)"].min(), df["小单净流入(万)"].min(), df["中单净流入(万)"].min()) * 1.2
    y_max = max(df["主力净流入(万)"].max(), df["小单净流入(万)"].max(), df["中单净流入(万)"].max()) * 1.2
    ax1.set_xlim(x_min, x_max)
    ax1.set_ylim(y_min, y_max)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax1.xaxis.set_major_locator(mdates.HourLocator(interval=1))

    # 绘制线条
    ax1.plot(df["time"], df["主力净流入(万)"], color=COLORS["red"], linewidth=2, alpha=0.95, label="主力净流入")
    ax1.plot(df["time"], df["小单净流入(万)"], color=COLORS["blue"], linewidth=1.5, alpha=0.8, label="小单净流入")
    ax1.plot(df["time"], df["中单净流入(万)"], color=COLORS["green"], linewidth=1.5, alpha=0.8, label="中单净流入")

    # 填充
    ax1.fill_between(df["time"], df["主力净流入(万)"], 0,
                     where=(df["主力净流入(万)"] >= 0), color=COLORS["red"], alpha=0.12, interpolate=True)
    ax1.fill_between(df["time"], df["主力净流入(万)"], 0,
                     where=(df["主力净流入(万)"] < 0), color=COLORS["green"], alpha=0.10, interpolate=True)

    ax1.legend(loc="upper left", fontsize=9, framealpha=0.9,
               facecolor=COLORS["card"], edgecolor=COLORS["border"], labelcolor=COLORS["text"])

    # 子图2：累计净流入
    ax2.set_ylabel("累计净流入（万元）", fontsize=11, color=COLORS["text_secondary"])
    ax2.set_title("主力资金累计净流入", fontsize=13, fontweight="bold", color=COLORS["text"], loc="left")

    cum_min = df["主力累计(万)"].min() * 1.2
    cum_max = df["主力累计(万)"].max() * 1.2
    ax2.set_xlim(x_min, x_max)
    ax2.set_ylim(cum_min, cum_max)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax2.xaxis.set_major_locator(mdates.HourLocator(interval=1))

    ax2.plot(df["time"], df["主力累计(万)"], color=COLORS["orange"], linewidth=2, label="主力累计净流入")
    ax2.fill_between(df["time"], df["主力累计(万)"], 0,
                     where=(df["主力累计(万)"] >= 0), color=COLORS["orange"], alpha=0.12, interpolate=True)

    ax2.legend(loc="upper left", fontsize=9, framealpha=0.9,
               facecolor=COLORS["card"], edgecolor=COLORS["border"], labelcolor=COLORS["text"])

    # 统计面板
    ax_stats.set_xlim(0, 1)
    ax_stats.set_ylim(0, 1)
    ax_stats.text(0.5, 0.95, "关键指标", fontsize=12, fontweight="bold",
                  color=COLORS["text"], ha="center", va="top", transform=ax_stats.transAxes)
    ax_stats.axhline(y=0.88, xmin=0.1, xmax=0.9, color=COLORS["border"], linewidth=0.8, alpha=0.6)

    stats_labels = ["主力净流入", "小单净流入", "中单净流入", "主力累计"]
    stats_values = [df["主力净流入(万)"].iloc[-1], df["小单净流入(万)"].iloc[-1],
                    df["中单净流入(万)"].iloc[-1], df["主力累计(万)"].iloc[-1]]

    for i, (label, val) in enumerate(zip(stats_labels, stats_values)):
        y_pos = 0.75 - i * 0.2
        ax_stats.text(0.08, y_pos, label, fontsize=9, color=COLORS["text_dim"],
                      va="center", transform=ax_stats.transAxes)
        color = COLORS["red_bright"] if val >= 0 else COLORS["green_bright"]
        ax_stats.text(0.92, y_pos, f"{val:.0f}万", fontsize=11, fontweight="bold",
                      color=color, ha="right", va="center", transform=ax_stats.transAxes,
                      path_effects=[pe.withStroke(linewidth=2, foreground=COLORS["card"])])

    # 信息面板
    ax_info.set_xlim(0, 1)
    ax_info.set_ylim(0, 1)
    ax_info.text(0.5, 0.95, "数据信息", fontsize=12, fontweight="bold",
                 color=COLORS["text"], ha="center", va="top", transform=ax_info.transAxes)
    ax_info.axhline(y=0.88, xmin=0.1, xmax=0.9, color=COLORS["border"], linewidth=0.8, alpha=0.6)

    info_lines = ["股票: 贵州茅台（600519）", f"数据点: {n} 个", "时间: 09:30 - 15:00", "帧率: 24 FPS"]
    for i, line in enumerate(info_lines):
        y_pos = 0.72 - i * 0.18
        ax_info.text(0.08, y_pos, line, fontsize=9, color=COLORS["text_dim"],
                     va="center", transform=ax_info.transAxes)

    # 保存
    os.makedirs("charts", exist_ok=True)
    save_path = "charts/preview_stock.png"
    plt.savefig(save_path, dpi=120, bbox_inches='tight', facecolor=COLORS["bg"])
    plt.close()
    print(f"预览图已保存: {save_path}")
    return save_path


if __name__ == "__main__":
    generate_preview()
