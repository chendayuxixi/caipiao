# -*- coding: utf-8 -*-
"""
测试板块折线图动画 - 专业量化风格 v2.0
Bloomberg/Wind终端风格
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.dates as mdates
import matplotlib.patheffects as pe
from datetime import datetime

# ── 专业量化配色方案 (Bloomberg Terminal 风格) ──────────────────
COLORS = {
    # 背景层次
    "bg":           "#0A0E14",   # 主背景 (更深)
    "bg_secondary": "#0D1219",   # 次级背景
    "card":         "#131A24",   # 卡片背景
    "card_hover":   "#1A2332",   # 卡片悬停

    # 网格与边框
    "grid":         "#1E2A38",   # 主网格线
    "grid_minor":   "#151D28",   # 次要网格
    "border":       "#2A3A4E",   # 边框
    "border_light": "#3A4F6A",   # 亮边框

    # 文字层次
    "text":         "#E6EDF3",   # 主文字 (高对比)
    "text_secondary": "#B0BAC5", # 次要文字
    "text_dim":     "#768390",   # 暗淡文字
    "text_muted":   "#545D68",   # 更暗文字

    # 金融配色 (专业级)
    "red":          "#FF4757",   # 涨/流入 (醒目红)
    "red_bright":   "#FF6B81",   # 涨/流入 亮
    "red_glow":     "#FF475740", # 红色辉光
    "red_fill":     "#FF475718", # 红色填充

    "green":        "#2ED573",   # 跌/流出 (醒目绿)
    "green_bright":  "#7BED9F",  # 跌/流出 亮
    "green_glow":   "#2ED57340", # 绿色辉光
    "green_fill":   "#2ED57318", # 绿色填充

    # 功能色
    "blue":         "#3498DB",   # 主蓝
    "blue_bright":  "#5DADE2",   # 亮蓝
    "blue_glow":    "#3498DB30", # 蓝色辉光

    "orange":       "#F39C12",   # 累计线 (醒目橙)
    "orange_bright": "#F1C40F",  # 亮橙
    "orange_glow":  "#F39C1230", # 橙色辉光

    "purple":       "#9B59B6",   # 辅助紫
    "purple_bright": "#BB8FCE",  # 亮紫

    "cyan":         "#1ABC9C",   # 辅助青
    "cyan_bright":  "#48C9B0",   # 亮青
    "cyan_glow":    "#1ABC9C30", # 青色辉光

    "yellow":       "#F1C40F",   # 高亮黄
    "yellow_bright": "#F4D03F",  # 亮黄

    # 特殊效果
    "glow_white":   "#FFFFFF15", # 白色辉光
    "shadow":       "#00000040", # 阴影
}

# ── 字体设置 (专业金融终端) ──────────────────────────────────────
plt.rcParams["font.sans-serif"] = [
    "Microsoft YaHei",  # 中文优先
    "SimHei",
    "Arial Unicode MS",
    "DejaVu Sans",      # 英文备选
]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.weight"] = "normal"


def _apply_dark_style(fig, axes):
    """应用专业深色主题到图表 (Bloomberg Terminal 风格)"""
    fig.patch.set_facecolor(COLORS["bg"])

    for ax in axes:
        ax.set_facecolor(COLORS["card"])

        # 坐标轴样式
        ax.tick_params(
            colors=COLORS["text_dim"],
            labelsize=9,
            length=4,
            width=0.8,
            direction='out'
        )

        # 标签样式
        ax.xaxis.label.set_color(COLORS["text_secondary"])
        ax.xaxis.label.set_fontsize(11)
        ax.yaxis.label.set_color(COLORS["text_secondary"])
        ax.yaxis.label.set_fontsize(11)

        # 标题样式
        ax.title.set_color(COLORS["text"])
        ax.title.set_fontsize(13)
        ax.title.set_fontweight("bold")

        # 边框样式
        for spine in ax.spines.values():
            spine.set_color(COLORS["border"])
            spine.set_linewidth(0.8)
            spine.set_linestyle('-')

        # 网格样式 (专业级)
        ax.grid(True, color=COLORS["grid"], alpha=0.5, linewidth=0.6)
        ax.set_axisbelow(True)  # 网格在数据下方

        # 零线样式
        ax.axhline(y=0, color=COLORS["border_light"],
                   linestyle="-", linewidth=1.0, alpha=0.8)


def _ease_out_cubic(t):
    """三次缓出函数 (更平滑)"""
    return 1 - (1 - t) ** 3


def create_sector_line_animation(sector_data=None, times=None, save_path=None, duration=12):
    """
    创建板块资金流向折线图动画 - 专业量化风格

    Parameters:
    -----------
    sector_data: dict
        板块数据 {板块名称: [分时数据列表]}
    times: DatetimeIndex
        时间序列
    save_path: str
        保存路径
    duration: int
        动画时长（秒），默认12秒
    """
    if sector_data is None:
        # 使用模拟数据
        morning_times = pd.date_range(start="2026-06-18 09:30", end="2026-06-18 11:30", freq="5min")
        afternoon_times = pd.date_range(start="2026-06-18 13:00", end="2026-06-18 15:00", freq="5min")
        times = pd.DatetimeIndex(morning_times.tolist() + afternoon_times.tolist())
        n = len(times)

        np.random.seed(42)
        sector_data = {
            "半导体": np.cumsum(np.random.randn(n) * 2) + 10,
            "人工智能": np.cumsum(np.random.randn(n) * 1.5) + 8,
            "新能源": np.cumsum(np.random.randn(n) * 1.8) - 5,
            "白酒": np.cumsum(np.random.randn(n) * 1.2) + 12,
            "医药": np.cumsum(np.random.randn(n) * 1.0) + 3,
            "军工": np.cumsum(np.random.randn(n) * 1.5) - 8,
            "汽车": np.cumsum(np.random.randn(n) * 0.8) + 2,
            "房地产": np.cumsum(np.random.randn(n) * 2.5) - 15,
            "银行": np.cumsum(np.random.randn(n) * 0.6) + 5,
            "证券": np.cumsum(np.random.randn(n) * 2.0) + 15,
        }

    n = len(times)
    fps = 24
    total_frames = duration * fps

    # ── 创建图表 (专业布局) ──────────────────────────────────────
    fig = plt.figure(figsize=(18, 10), dpi=130)
    gs = fig.add_gridspec(
        2, 2,
        height_ratios=[3.5, 1],
        width_ratios=[3.5, 1],
        hspace=0.22,
        wspace=0.22,
        left=0.05,
        right=0.95,
        top=0.88,
        bottom=0.08
    )

    ax_main = fig.add_subplot(gs[0, 0])    # 主折线图
    ax_rank = fig.add_subplot(gs[0, 1])    # 排名面板
    ax_bar = fig.add_subplot(gs[1, :])     # 进度条

    axes = [ax_main, ax_rank, ax_bar]
    _apply_dark_style(fig, axes)

    for ax in [ax_rank, ax_bar]:
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_linewidth(0.6)
            spine.set_color(COLORS["border"])

    # ── 专业级标题 ──────────────────────────────────────────────
    fig.suptitle(
        "行业板块资金流向对比分析",
        fontsize=20,
        fontweight="bold",
        color=COLORS["text"],
        y=0.94
    )

    fig.text(
        0.5, 0.91,
        f"数据时间: {times[0].strftime('%Y-%m-%d %H:%M')} - {times[-1].strftime('%H:%M')}",
        fontsize=10,
        color=COLORS["text_dim"],
        ha='center'
    )

    # ── 主折线图 (专业级) ──────────────────────────────────────
    ax_main.set_xlabel("时间", fontsize=11, color=COLORS["text_secondary"])
    ax_main.set_ylabel("主力累计净流入（亿元）", fontsize=11, color=COLORS["text_secondary"])

    # 专业配色（10个板块）- 金融终端风格
    sector_colors = [
        {"main": "#FF4757", "glow": "#FF475760"},  # 红
        {"main": "#3498DB", "glow": "#3498DB60"},  # 蓝
        {"main": "#2ED573", "glow": "#2ED57360"},  # 绿
        {"main": "#F39C12", "glow": "#F39C1260"},  # 橙
        {"main": "#9B59B6", "glow": "#9B59B660"},  # 紫
        {"main": "#FF6B81", "glow": "#FF6B8160"},  # 亮红
        {"main": "#1ABC9C", "glow": "#1ABC9C60"},  # 青
        {"main": "#E74C3C", "glow": "#E74C3C60"},  # 深红
        {"main": "#F1C40F", "glow": "#F1C40F60"},  # 黄
        {"main": "#5DADE2", "glow": "#5DADE260"},  # 亮蓝
    ]

    lines = {}
    glows = {}
    markers = {}
    for i, (name, values) in enumerate(sector_data.items()):
        # 辉光线
        glow, = ax_main.plot([], [], color=sector_colors[i]["glow"],
                             linewidth=5, alpha=0.4, zorder=4)
        glows[name] = glow

        # 主线
        line, = ax_main.plot([], [], label=name, color=sector_colors[i]["main"],
                             linewidth=2.2, alpha=0.95, zorder=6)
        lines[name] = line

        # 标记点
        marker, = ax_main.plot([], [], "o", color=sector_colors[i]["main"],
                               markersize=6, markeredgecolor='white',
                               markeredgewidth=1.5, zorder=10)
        markers[name] = marker

    ax_main.axhline(y=0, color=COLORS["border_light"], linestyle="-",
                    linewidth=1.0, alpha=0.8)

    all_values = np.concatenate([np.array(v) for v in sector_data.values()])
    y_min = all_values.min() * 1.2
    y_max = all_values.max() * 1.2
    ax_main.set_xlim(times[0], times[-1])
    ax_main.set_ylim(y_min, y_max)
    ax_main.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax_main.xaxis.set_major_locator(mdates.HourLocator(interval=1))

    # 专业级图例
    ax_main.legend(
        loc="upper left",
        fontsize=8,
        framealpha=0.9,
        facecolor=COLORS["card"],
        edgecolor=COLORS["border"],
        labelcolor=COLORS["text"],
        ncol=2,
        borderaxespad=0.5
    )

    # ── 排名面板 (专业级) ──────────────────────────────────────
    ax_rank.set_xlim(0, 1)
    ax_rank.set_ylim(0, 1)

    # 面板标题
    ax_rank.text(
        0.5, 0.95,
        "实时排名",
        fontsize=12,
        fontweight="bold",
        color=COLORS["text"],
        ha="center", va="top",
        transform=ax_rank.transAxes
    )

    # 分隔线
    ax_rank.axhline(y=0.90, xmin=0.1, xmax=0.9,
                    color=COLORS["border"], linewidth=0.8, alpha=0.6)

    rank_texts = []
    for i, name in enumerate(sector_data.keys()):
        y_pos = 0.85 - i * 0.08

        # 排名序号
        rank_num = ax_rank.text(
            0.05, y_pos, f"{i+1}.",
            fontsize=9,
            color=COLORS["text_muted"],
            va="center",
            transform=ax_rank.transAxes
        )

        # 板块名称
        t = ax_rank.text(
            0.15, y_pos, name,
            fontsize=9,
            color=COLORS["text_dim"],
            va="center",
            transform=ax_rank.transAxes
        )

        # 数值
        val_t = ax_rank.text(
            0.92, y_pos, "0.00亿",
            fontsize=10,
            fontweight="bold",
            color=COLORS["text"],
            ha="right", va="center",
            transform=ax_rank.transAxes,
            path_effects=[
                pe.withStroke(linewidth=2, foreground=COLORS["card"])
            ]
        )

        rank_texts.append((rank_num, t, val_t))

    # ── 进度条 (专业级) ────────────────────────────────────────
    ax_bar.set_xlim(0, 1)
    ax_bar.set_ylim(0, 1)

    # 进度条背景
    ax_bar.fill_between([0, 1], 0.2, 0.8, color=COLORS["grid"], alpha=0.5)

    # 进度条
    progress_bar = ax_bar.fill_between([0, 0], 0.2, 0.8, color=COLORS["blue"], alpha=0.7)

    # 进度条边框
    ax_bar.plot([0, 1, 1, 0, 0], [0.2, 0.2, 0.8, 0.8, 0.2],
                color=COLORS["border"], linewidth=0.8, alpha=0.6)

    # 进度文字
    progress_text = ax_bar.text(
        0.5, 0.5, "0%",
        fontsize=10,
        fontweight="bold",
        color=COLORS["text"],
        ha="center", va="center",
        transform=ax_bar.transAxes
    )

    # 时间标签
    time_text = ax_bar.text(
        0.02, 0.5, "00:00",
        fontsize=9,
        color=COLORS["text_dim"],
        ha="left", va="center",
        transform=ax_bar.transAxes
    )

    # ── 动画更新函数 ──────────────────────────────────────────
    def update(frame):
        nonlocal progress_bar

        t = frame / max(total_frames - 1, 1)
        eased_t = _ease_out_cubic(t)
        idx = int(eased_t * (n - 1))
        idx = min(idx, n - 1)

        current_times = times[:idx + 1]

        # 更新线条和标记
        for name, values in sector_data.items():
            lines[name].set_data(current_times, values[:idx + 1])
            glows[name].set_data(current_times, values[:idx + 1])
            if idx < len(values):
                markers[name].set_data([current_times[-1]], [values[idx]])

        # 更新排名
        if idx < n:
            current_vals = {name: values[idx] for name, values in sector_data.items()}
            sorted_sectors = sorted(current_vals.items(), key=lambda x: x[1], reverse=True)
            for i, (name, val) in enumerate(sorted_sectors):
                rank_texts[i][1].set_text(name)
                rank_texts[i][2].set_text(f"{val:.2f}亿")
                color = COLORS["red_bright"] if val >= 0 else COLORS["green_bright"]
                rank_texts[i][2].set_color(color)

                # 更新排名序号颜色
                if i == 0:
                    rank_texts[i][0].set_color(COLORS["yellow_bright"])
                elif i == 1:
                    rank_texts[i][0].set_color(COLORS["text_secondary"])
                elif i == 2:
                    rank_texts[i][0].set_color(COLORS["orange_bright"])
                else:
                    rank_texts[i][0].set_color(COLORS["text_muted"])

        # 更新进度条
        progress_bar.remove()
        progress_bar = ax_bar.fill_between([0, t], 0.2, 0.8, color=COLORS["blue"], alpha=0.7)
        progress_text.set_text(f"{int(t * 100)}%")

        # 更新时间标签
        if idx < len(times):
            time_text.set_text(times[idx].strftime("%H:%M"))

        all_artists = list(lines.values()) + list(glows.values()) + list(markers.values())
        all_artists.extend([progress_bar, progress_text, time_text])
        for rank_num, t_text, v_text in rank_texts:
            all_artists.extend([rank_num, t_text, v_text])
        return all_artists

    # ── 生成动画 ──────────────────────────────────────────────
    ani = animation.FuncAnimation(
        fig, update,
        frames=total_frames,
        interval=1000 // fps,
        blit=False,
        repeat=False
    )

    if save_path:
        ani.save(save_path, writer="pillow", fps=fps)
        print(f"  动画已保存: {save_path}")
        print(f"  播放时长: {duration}秒")
        plt.close()
    else:
        plt.show()

    return ani


if __name__ == "__main__":
    print("=" * 70)
    print("板块资金流向动画测试 - 专业量化风格 v2.0")
    print("Bloomberg/Wind终端风格")
    print("=" * 70)

    os.makedirs("charts", exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")

    print("\n生成板块资金流向折线图动画...")
    save_path = f"charts/test_sector_lines_{today}_flow.gif"
    create_sector_line_animation(save_path=save_path, duration=12)

    print("\n测试完成！请查看 charts/ 目录下的GIF文件")
    print("=" * 70)
