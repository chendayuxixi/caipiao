# -*- coding: utf-8 -*-
"""
测试动画生成功能（使用模拟数据）- 专业量化风格 v2.0
Bloomberg/Wind终端风格的专业金融数据可视化
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


def _ease_in_out_cubic(t):
    """三次缓入缓出函数"""
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - pow(-2 * t + 2, 3) / 2


def generate_mock_data():
    """生成模拟数据"""
    morning_times = pd.date_range(start="2026-06-18 09:30", end="2026-06-18 11:30", freq="1min")
    afternoon_times = pd.date_range(start="2026-06-18 13:00", end="2026-06-18 15:00", freq="1min")
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
        "大单净流入": main_flow * 0.7 + np.cumsum(np.random.randn(n) * 400000),
        "超大单净流入": main_flow * 0.3 + np.cumsum(np.random.randn(n) * 150000),
    })

    return df


def create_stock_animation(df, stock_name="贵州茅台", stock_code="600519",
                           save_path=None, duration=12):
    """创建个股资金流向动画 - 专业量化风格"""
    if df.empty:
        print(f"  {stock_name} 无数据，跳过动画生成")
        return

    df = df.copy()
    for col in ["主力净流入", "小单净流入", "中单净流入", "大单净流入", "超大单净流入"]:
        df[f"{col}(万)"] = df[col] / 10000

    df["主力累计(万)"] = df["主力净流入(万)"].cumsum()
    n = len(df)
    fps = 24
    total_frames = duration * fps

    # ── 创建图表 (专业布局) ──────────────────────────────────────
    fig = plt.figure(figsize=(18, 11), dpi=130)

    # 专业级网格布局
    gs = fig.add_gridspec(
        2, 2,
        height_ratios=[2.8, 2.8],
        width_ratios=[3.2, 1],
        hspace=0.30,
        wspace=0.22,
        left=0.05,
        right=0.95,
        top=0.88,
        bottom=0.10
    )

    ax1 = fig.add_subplot(gs[0, 0])    # 分时资金净流入
    ax2 = fig.add_subplot(gs[1, 0])    # 累计净流入
    ax_stats = fig.add_subplot(gs[0, 1])  # 统计面板
    ax_info = fig.add_subplot(gs[1, 1])   # 信息面板

    axes = [ax1, ax2, ax_stats, ax_info]
    _apply_dark_style(fig, axes)

    # 隐藏统计/信息面板的坐标轴
    for ax in [ax_stats, ax_info]:
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_linewidth(0.6)
            spine.set_color(COLORS["border"])

    # ── 专业级标题 ──────────────────────────────────────────────
    # 主标题
    fig.suptitle(
        f"{stock_name}（{stock_code}）资金流向分析",
        fontsize=20,
        fontweight="bold",
        color=COLORS["text"],
        y=0.94
    )

    # 副标题 (时间信息)
    fig.text(
        0.5, 0.91,
        f"数据时间: {df['time'].min().strftime('%Y-%m-%d %H:%M')} - {df['time'].max().strftime('%H:%M')}",
        fontsize=10,
        color=COLORS["text_dim"],
        ha='center'
    )

    # ── 子图1：分时资金净流入 (专业级) ─────────────────────────
    ax1.set_ylabel("净流入金额（万元）", fontsize=11, color=COLORS["text_secondary"])
    ax1.set_title(
        "分时资金净流入",
        fontsize=13,
        fontweight="bold",
        color=COLORS["text"],
        pad=12,
        loc="left"
    )

    # 添加时间标注
    ax1.text(
        0.98, 0.95,
        "实时",
        transform=ax1.transAxes,
        fontsize=9,
        color=COLORS["cyan_bright"],
        ha='right', va='top',
        bbox=dict(boxstyle='round,pad=0.3', facecolor=COLORS["cyan_glow"], edgecolor='none')
    )

    x_min, x_max = df["time"].min(), df["time"].max()
    y_min = min(df["主力净流入(万)"].min(), df["小单净流入(万)"].min(),
                df["中单净流入(万)"].min()) * 1.2
    y_max = max(df["主力净流入(万)"].max(), df["小单净流入(万)"].max(),
                df["中单净流入(万)"].max()) * 1.2
    ax1.set_xlim(x_min, x_max)
    ax1.set_ylim(y_min, y_max)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax1.xaxis.set_major_locator(mdates.HourLocator(interval=1))

    # 专业级线条 (带辉光)
    line_main, = ax1.plot([], [], label="主力净流入",
                          color=COLORS["red"], linewidth=2.5, alpha=0.95, zorder=6)
    line_main_glow, = ax1.plot([], [], color=COLORS["red_glow"],
                               linewidth=6, alpha=0.4, zorder=5)

    line_small, = ax1.plot([], [], label="小单净流入",
                           color=COLORS["blue"], linewidth=1.8, alpha=0.80, zorder=4)
    line_medium, = ax1.plot([], [], label="中单净流入",
                            color=COLORS["green"], linewidth=1.8, alpha=0.80, zorder=4)

    # 填充层（渐变效果）
    fill_main = ax1.fill_between([], [], [], color=COLORS["red"], alpha=0.12)
    fill_main_neg = ax1.fill_between([], [], [], color=COLORS["green"], alpha=0.10)

    # 值标记 (带辉光)
    marker_main, = ax1.plot([], [], "o", color=COLORS["red_bright"], markersize=7,
                            markeredgecolor='white', markeredgewidth=1.5,
                            zorder=15, alpha=0.95)
    glow_main, = ax1.plot([], [], "o", color=COLORS["red_glow"],
                          markersize=12, alpha=0.3, zorder=14)
    text_main = ax1.annotate(
        "", xy=(0, 0),
        fontsize=9,
        fontweight="bold",
        color=COLORS["red_bright"],
        ha="left", va="bottom",
        path_effects=[
            pe.withStroke(linewidth=3, foreground=COLORS["card"]),
            pe.withSimplePatchShadow(
                offset=(1, -1),
                shadow_rgbFace=COLORS["shadow"],
                alpha=0.5
            )
        ]
    )

    marker_small, = ax1.plot([], [], "o", color=COLORS["blue_bright"], markersize=6,
                             markeredgecolor='white', markeredgewidth=1.5,
                             zorder=15, alpha=0.95)
    glow_small, = ax1.plot([], [], "o", color=COLORS["blue_glow"],
                           markersize=10, alpha=0.3, zorder=14)
    text_small = ax1.annotate(
        "", xy=(0, 0),
        fontsize=9,
        fontweight="bold",
        color=COLORS["blue_bright"],
        ha="left", va="bottom",
        path_effects=[
            pe.withStroke(linewidth=3, foreground=COLORS["card"]),
            pe.withSimplePatchShadow(
                offset=(1, -1),
                shadow_rgbFace=COLORS["shadow"],
                alpha=0.5
            )
        ]
    )

    # 专业级图例
    ax1.legend(
        loc="upper left",
        fontsize=9,
        framealpha=0.9,
        facecolor=COLORS["card"],
        edgecolor=COLORS["border"],
        labelcolor=COLORS["text"],
        borderaxespad=0.5,
        handlelength=1.5,
        handleheight=1.0
    )

    # ── 子图2：主力累计净流入 (专业级) ─────────────────────────
    ax2.set_ylabel("累计净流入（万元）", fontsize=11, color=COLORS["text_secondary"])
    ax2.set_title(
        "主力资金累计净流入",
        fontsize=13,
        fontweight="bold",
        color=COLORS["text"],
        pad=12,
        loc="left"
    )

    # 添加累计标注
    ax2.text(
        0.98, 0.95,
        "累计",
        transform=ax2.transAxes,
        fontsize=9,
        color=COLORS["orange_bright"],
        ha='right', va='top',
        bbox=dict(boxstyle='round,pad=0.3', facecolor=COLORS["orange_glow"], edgecolor='none')
    )

    cum_min = df["主力累计(万)"].min() * 1.2
    cum_max = df["主力累计(万)"].max() * 1.2
    ax2.set_xlim(x_min, x_max)
    ax2.set_ylim(cum_min, cum_max)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax2.xaxis.set_major_locator(mdates.HourLocator(interval=1))

    # 累计线 (带辉光)
    line_cum, = ax2.plot([], [], color=COLORS["orange"], linewidth=2.5,
                         label="主力累计净流入", zorder=6)
    line_cum_glow, = ax2.plot([], [], color=COLORS["orange_glow"],
                              linewidth=6, alpha=0.4, zorder=5)

    fill_cum = ax2.fill_between([], [], [], color=COLORS["orange"], alpha=0.12)

    marker_cum, = ax2.plot([], [], "o", color=COLORS["yellow_bright"], markersize=7,
                           markeredgecolor='white', markeredgewidth=1.5,
                           zorder=15, alpha=0.95)
    glow_cum, = ax2.plot([], [], "o", color=COLORS["orange_glow"],
                         markersize=12, alpha=0.3, zorder=14)
    text_cum = ax2.annotate(
        "", xy=(0, 0),
        fontsize=9,
        fontweight="bold",
        color=COLORS["yellow_bright"],
        ha="left", va="bottom",
        path_effects=[
            pe.withStroke(linewidth=3, foreground=COLORS["card"]),
            pe.withSimplePatchShadow(
                offset=(1, -1),
                shadow_rgbFace=COLORS["shadow"],
                alpha=0.5
            )
        ]
    )

    ax2.legend(
        loc="upper left",
        fontsize=9,
        framealpha=0.9,
        facecolor=COLORS["card"],
        edgecolor=COLORS["border"],
        labelcolor=COLORS["text"],
        borderaxespad=0.5
    )

    # ── 统计面板 (专业级) ──────────────────────────────────────
    ax_stats.set_xlim(0, 1)
    ax_stats.set_ylim(0, 1)

    # 面板标题
    ax_stats.text(
        0.5, 0.95,
        "关键指标",
        fontsize=12,
        fontweight="bold",
        color=COLORS["text"],
        ha="center", va="top",
        transform=ax_stats.transAxes
    )

    # 分隔线
    ax_stats.axhline(y=0.88, xmin=0.1, xmax=0.9,
                     color=COLORS["border"], linewidth=0.8, alpha=0.6)

    stats_labels = ["主力净流入", "小单净流入", "中单净流入", "主力累计"]
    stats_texts = []
    stats_glows = []

    for i, label in enumerate(stats_labels):
        y_pos = 0.78 - i * 0.22

        # 标签
        ax_stats.text(
            0.08, y_pos, label,
            fontsize=9,
            color=COLORS["text_dim"],
            va="center",
            transform=ax_stats.transAxes
        )

        # 数值 (带辉光效果)
        t = ax_stats.text(
            0.92, y_pos, "0万",
            fontsize=11,
            fontweight="bold",
            color=COLORS["text"],
            ha="right", va="center",
            transform=ax_stats.transAxes,
            path_effects=[
                pe.withStroke(linewidth=2, foreground=COLORS["card"])
            ]
        )
        stats_texts.append(t)

        # 辉光背景
        glow = ax_stats.fill_between(
            [0.05, 0.95], [y_pos - 0.08, y_pos - 0.08],
            [y_pos + 0.08, y_pos + 0.08],
            color=COLORS["glow_white"],
            alpha=0,
            transform=ax_stats.transAxes
        )
        stats_glows.append(glow)

    # ── 信息面板 (专业级) ──────────────────────────────────────
    ax_info.set_xlim(0, 1)
    ax_info.set_ylim(0, 1)

    ax_info.text(
        0.5, 0.95,
        "数据信息",
        fontsize=12,
        fontweight="bold",
        color=COLORS["text"],
        ha="center", va="top",
        transform=ax_info.transAxes
    )

    # 分隔线
    ax_info.axhline(y=0.88, xmin=0.1, xmax=0.9,
                    color=COLORS["border"], linewidth=0.8, alpha=0.6)

    info_lines = [
        f"股票: {stock_name}（{stock_code}）",
        f"数据点: {n} 个",
        f"时间: {df['time'].min().strftime('%H:%M')} - {df['time'].max().strftime('%H:%M')}",
        f"帧数: {duration * fps} 帧 / {duration}秒",
        f"帧率: {fps} FPS",
    ]
    for i, line in enumerate(info_lines):
        y_pos = 0.75 - i * 0.16
        ax_info.text(
            0.08, y_pos, line,
            fontsize=9,
            color=COLORS["text_dim"],
            va="center",
            transform=ax_info.transAxes
        )

        # 添加小图标指示器
        if i == 0:
            ax_info.plot(0.03, y_pos, "s", color=COLORS["blue_bright"],
                         markersize=4, transform=ax_info.transAxes)
        elif i == 1:
            ax_info.plot(0.03, y_pos, "s", color=COLORS["green_bright"],
                         markersize=4, transform=ax_info.transAxes)
        elif i == 2:
            ax_info.plot(0.03, y_pos, "s", color=COLORS["orange_bright"],
                         markersize=4, transform=ax_info.transAxes)
        elif i == 3:
            ax_info.plot(0.03, y_pos, "s", color=COLORS["purple_bright"],
                         markersize=4, transform=ax_info.transAxes)
        elif i == 4:
            ax_info.plot(0.03, y_pos, "s", color=COLORS["cyan_bright"],
                         markersize=4, transform=ax_info.transAxes)

    # ── 底部免责声明 ──────────────────────────────────────────
    fig.text(
        0.5, 0.02,
        "免责声明：本图表仅供参考，不构成任何投资建议。数据来源于公开市场信息，不保证其准确性和完整性。投资有风险，入市需谨慎。",
        fontsize=7,
        color=COLORS["text_muted"],
        ha='center',
        va='bottom'
    )

    # ── 动画更新 ──────────────────────────────────────────────
    def update(frame):
        nonlocal fill_main, fill_main_neg, fill_cum

        t = frame / max(total_frames - 1, 1)
        eased_t = _ease_out_cubic(t)
        idx = min(int(eased_t * (n - 1)), n - 1)

        current_df = df.iloc[:idx + 1]

        # 线条
        line_main.set_data(current_df["time"], current_df["主力净流入(万)"])
        line_main_glow.set_data(current_df["time"], current_df["主力净流入(万)"])
        line_small.set_data(current_df["time"], current_df["小单净流入(万)"])
        line_medium.set_data(current_df["time"], current_df["中单净流入(万)"])

        # 填充
        fill_main.remove()
        fill_main_neg.remove()
        fill_main = ax1.fill_between(
            current_df["time"], current_df["主力净流入(万)"], 0,
            where=(current_df["主力净流入(万)"] >= 0),
            color=COLORS["red"], alpha=0.12, interpolate=True
        )
        fill_main_neg = ax1.fill_between(
            current_df["time"], current_df["主力净流入(万)"], 0,
            where=(current_df["主力净流入(万)"] < 0),
            color=COLORS["green"], alpha=0.10, interpolate=True
        )

        # 累计
        line_cum.set_data(current_df["time"], current_df["主力累计(万)"])
        line_cum_glow.set_data(current_df["time"], current_df["主力累计(万)"])
        fill_cum.remove()
        fill_cum = ax2.fill_between(
            current_df["time"], current_df["主力累计(万)"], 0,
            where=(current_df["主力累计(万)"] >= 0),
            color=COLORS["orange"], alpha=0.12, interpolate=True
        )

        # 标记
        if len(current_df) > 0:
            last_t = current_df["time"].iloc[-1]
            main_v = current_df["主力净流入(万)"].iloc[-1]
            small_v = current_df["小单净流入(万)"].iloc[-1]
            cum_v = current_df["主力累计(万)"].iloc[-1]

            marker_main.set_data([last_t], [main_v])
            glow_main.set_data([last_t], [main_v])
            text_main.set_position((last_t, main_v))
            text_main.set_text(f" {main_v:.0f}")

            marker_small.set_data([last_t], [small_v])
            glow_small.set_data([last_t], [small_v])
            text_small.set_position((last_t, small_v))
            text_small.set_text(f" {small_v:.0f}")

            marker_cum.set_data([last_t], [cum_v])
            glow_cum.set_data([last_t], [cum_v])
            text_cum.set_position((last_t, cum_v))
            text_cum.set_text(f" {cum_v:.0f}")

            # 统计
            vals = [
                current_df["主力净流入(万)"].iloc[-1],
                current_df["小单净流入(万)"].iloc[-1],
                current_df["中单净流入(万)"].iloc[-1],
                current_df["主力累计(万)"].iloc[-1],
            ]
            for i, v in enumerate(vals):
                stats_texts[i].set_text(f"{v:.0f}万")
                stats_texts[i].set_color(COLORS["red_bright"] if v >= 0 else COLORS["green_bright"])

                # 更新辉光背景
                if v >= 0:
                    stats_glows[i].set_alpha(0.05)
                else:
                    stats_glows[i].set_alpha(0.03)

        return (
            line_main, line_main_glow, line_small, line_medium,
            line_cum, line_cum_glow,
            marker_main, glow_main, text_main,
            marker_small, glow_small, text_small,
            marker_cum, glow_cum, text_cum,
            fill_main, fill_main_neg, fill_cum
        )

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
        plt.close()
    else:
        plt.show()

    return ani


def create_sector_animation(save_path=None, speed="slow", duration=12):
    """
    创建板块资金流向动画 - 专业量化风格
    speed: slow(慢约8秒), normal(正常约3.6秒), fast(快约1.2秒)
    """
    sectors = [
        ("半导体", 2.5, 15.3),
        ("人工智能", 1.8, 12.1),
        ("新能源", -0.5, -8.2),
        ("白酒", 3.2, 18.5),
        ("医药", 1.1, 6.7),
        ("军工", -1.2, -9.3),
        ("汽车", 0.8, 4.5),
        ("房地产", -2.1, -14.2),
        ("银行", 1.5, 10.8),
        ("证券", 2.8, 16.2),
    ]

    df = pd.DataFrame(sectors, columns=["板块名称", "涨跌幅", "主力净流入(亿)"])
    df = df.sort_values("主力净流入(亿)", ascending=True)

    names = df["板块名称"].values
    values = df["主力净流入(亿)"].values
    n = len(names)

    fps = 24
    total_frames = duration * fps

    # ── 创建图表 (专业布局) ──────────────────────────────────────
    fig = plt.figure(figsize=(16, 10), dpi=130)
    gs = fig.add_gridspec(
        1, 1,
        left=0.10,
        right=0.92,
        top=0.88,
        bottom=0.10
    )

    ax = fig.add_subplot(gs[0])

    _apply_dark_style(fig, [ax])

    # ── 专业级标题 ──────────────────────────────────────────────
    fig.suptitle(
        f"行业板块 · 主力资金净流入 TOP10",
        fontsize=20,
        fontweight="bold",
        color=COLORS["text"],
        y=0.94
    )

    fig.text(
        0.5, 0.91,
        f"数据时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        fontsize=10,
        color=COLORS["text_dim"],
        ha='center'
    )

    # ── 横向柱状图 (专业级) ────────────────────────────────────
    # 专业配色 (带辉光)
    bar_colors = []
    glow_colors = []
    for v in values:
        if v >= 0:
            bar_colors.append(COLORS["red"])
            glow_colors.append(COLORS["red_glow"])
        else:
            bar_colors.append(COLORS["green"])
            glow_colors.append(COLORS["green_glow"])

    # 辉光条
    bars_glow = ax.barh(
        range(n), np.zeros(n),
        color=glow_colors, alpha=0.4,
        height=0.7, edgecolor="none", zorder=2
    )

    # 主条
    bars = ax.barh(
        range(n), np.zeros(n),
        color=bar_colors, alpha=0.85,
        height=0.6, edgecolor="none", zorder=3
    )

    # 值标签 (带阴影)
    val_texts = []
    for i, v in enumerate(values):
        color = COLORS["red_bright"] if v >= 0 else COLORS["green_bright"]
        t = ax.text(
            0, i, "",
            fontsize=11,
            fontweight="bold",
            color=color,
            va="center",
            ha="left" if v >= 0 else "right",
            path_effects=[
                pe.withStroke(linewidth=3, foreground=COLORS["card"]),
                pe.withSimplePatchShadow(
                    offset=(1, -1),
                    shadow_rgbFace=COLORS["shadow"],
                    alpha=0.5
                )
            ]
        )
        val_texts.append(t)

    ax.set_yticks(range(n))
    ax.set_yticklabels(names, fontsize=11, color=COLORS["text"])
    ax.set_xlabel("主力净流入（亿元）", fontsize=11, color=COLORS["text_secondary"])
    ax.axvline(x=0, color=COLORS["border_light"], linestyle="-",
               linewidth=1.0, alpha=0.8)
    ax.grid(True, axis="x", color=COLORS["grid"], alpha=0.3, linewidth=0.5)

    x_max = max(abs(values)) * 1.3
    ax.set_xlim(-x_max, x_max)

    # ── 底部免责声明 ──────────────────────────────────────────
    fig.text(
        0.5, 0.02,
        "免责声明：本图表仅供参考，不构成任何投资建议。数据来源于公开市场信息，不保证其准确性和完整性。投资有风险，入市需谨慎。",
        fontsize=7,
        color=COLORS["text_muted"],
        ha='center',
        va='bottom'
    )

    # ── 动画更新 ──────────────────────────────────────────────
    def update(frame):

        t = frame / max(total_frames - 1, 1)
        eased_t = _ease_out_cubic(t)

        for i, bar in enumerate(bars):
            target_width = values[i] * eased_t
            bar.set_width(target_width)

            # 更新辉光条
            bars_glow[i].set_width(target_width)

            # 更新值标签（显示当前动画进度对应的值，而非最终值）
            if eased_t > 0.05:
                current_val = values[i] * eased_t
                val_texts[i].set_text(
                    f" {current_val:+.1f}亿" if current_val >= 0 else f" {current_val:.1f}亿"
                )
                x_pos = target_width + (x_max * 0.02) if current_val >= 0 else target_width - (x_max * 0.02)
                val_texts[i].set_x(x_pos)

        return list(bars) + list(bars_glow) + val_texts

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
        plt.close()
    else:
        plt.show()

    return ani


if __name__ == "__main__":
    print("=" * 70)
    print("资金流向动画测试 - 专业量化风格 v2.0")
    print("Bloomberg/Wind终端风格")
    print("=" * 70)

    os.makedirs("charts", exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")

    print("\n生成个股资金流向动画...")
    df = generate_mock_data()
    save_path = f"charts/test_stock_{today}_flow.gif"
    create_stock_animation(df, save_path=save_path)

    print("\n生成板块资金流向动画...")
    save_path = f"charts/test_sector_{today}_flow.gif"
    create_sector_animation(save_path=save_path, speed="slow")

    print("\n测试完成！请查看 charts/ 目录下的GIF文件")
    print("=" * 70)
