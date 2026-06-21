# -*- coding: utf-8 -*-
"""
资金流向动画生成器 - 专业量化风格 v2.0
在午盘和收盘后生成资金流向动画
专业级金融数据可视化，符合Bloomberg/Wind终端风格
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.dates as mdates
import matplotlib.patheffects as pe
from datetime import datetime
from fund_monitor import fetch_fund_flow, parse_fund_flow_data
from sector_monitor import fetch_sector_list, get_sector_top, fetch_sector_line_data, verify_sector_data
from config import STOCK_LIST, CHART_DIR
from theme import COLORS, LINE_COLORS, SECTOR_COLORS, apply_dark_style, ease_out_cubic

# 兼容旧名称
_apply_dark_style = apply_dark_style
_ease_out_cubic = ease_out_cubic


def create_stock_flow_animation(df, stock_code, stock_name, save_path=None, duration=12):
    """
    创建个股资金流向动画 - 专业量化风格

    Parameters:
    -----------
    df: DataFrame
        资金流向数据
    stock_code: str
        股票代码
    stock_name: str
        股票名称
    save_path: str
        保存路径
    duration: int
        动画时长（秒），默认12秒
    """
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

    # 采样帧索引（确保覆盖所有数据点）
    if n <= total_frames:
        frame_indices = np.arange(n)
    else:
        frame_indices = np.linspace(0, n - 1, total_frames, dtype=int)

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
    marker_main, glow_main, text_main = _add_value_marker(
        ax1, df["time"], df["主力净流入(万)"],
        COLORS["red_bright"], fmt="{:.0f}"
    )
    marker_small, glow_small, text_small = _add_value_marker(
        ax1, df["time"], df["小单净流入(万)"],
        COLORS["blue_bright"], fmt="{:.0f}"
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

    marker_cum, glow_cum, text_cum = _add_value_marker(
        ax2, df["time"], df["主力累计(万)"],
        COLORS["yellow_bright"], fmt="{:.0f}"
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
    stats_values = [0, 0, 0, 0]
    stats_texts = []
    stats_glows = []

    for i, (label, val) in enumerate(zip(stats_labels, stats_values)):
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
            0.92, y_pos, f"{val:.0f}万",
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
        f"时间范围: {df['time'].min().strftime('%H:%M')} - {df['time'].max().strftime('%H:%M')}",
        f"动画帧数: {len(frame_indices)} 帧",
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

    # ── 动画更新函数 ──────────────────────────────────────────
    def update(frame):
        nonlocal fill_main, fill_main_neg, fill_cum

        # 计算当前数据索引（带缓动）
        t = frame / max(total_frames - 1, 1)
        eased_t = _ease_out_cubic(t)
        idx = int(eased_t * (n - 1))
        idx = min(idx, n - 1)

        current_df = df.iloc[:idx + 1]

        # 更新分时线条
        line_main.set_data(current_df["time"], current_df["主力净流入(万)"])
        line_main_glow.set_data(current_df["time"], current_df["主力净流入(万)"])
        line_small.set_data(current_df["time"], current_df["小单净流入(万)"])
        line_medium.set_data(current_df["time"], current_df["中单净流入(万)"])

        # 更新填充
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

        # 更新累计线
        line_cum.set_data(current_df["time"], current_df["主力累计(万)"])
        line_cum_glow.set_data(current_df["time"], current_df["主力累计(万)"])
        fill_cum.remove()
        fill_cum = ax2.fill_between(
            current_df["time"], current_df["主力累计(万)"], 0,
            where=(current_df["主力累计(万)"] >= 0),
            color=COLORS["orange"], alpha=0.12, interpolate=True
        )

        # 更新值标记
        if len(current_df) > 0:
            _update_marker(marker_main, glow_main, text_main,
                          current_df["time"], current_df["主力净流入(万)"])
            _update_marker(marker_small, glow_small, text_small,
                          current_df["time"], current_df["小单净流入(万)"])
            _update_marker(marker_cum, glow_cum, text_cum,
                          current_df["time"], current_df["主力累计(万)"])

        # 更新统计面板
        if len(current_df) > 0:
            main_val = current_df["主力净流入(万)"].iloc[-1]
            small_val = current_df["小单净流入(万)"].iloc[-1]
            medium_val = current_df["中单净流入(万)"].iloc[-1]
            cum_val = current_df["主力累计(万)"].iloc[-1]

            stats_texts[0].set_text(f"{main_val:.0f}万")
            stats_texts[0].set_color(COLORS["red_bright"] if main_val >= 0 else COLORS["green_bright"])
            stats_texts[1].set_text(f"{small_val:.0f}万")
            stats_texts[1].set_color(COLORS["blue_bright"] if small_val >= 0 else COLORS["green_bright"])
            stats_texts[2].set_text(f"{medium_val:.0f}万")
            stats_texts[2].set_color(COLORS["green_bright"] if medium_val >= 0 else COLORS["red_bright"])
            stats_texts[3].set_text(f"{cum_val:.0f}万")
            stats_texts[3].set_color(COLORS["yellow_bright"] if cum_val >= 0 else COLORS["green_bright"])

            # 更新辉光背景
            for i, glow in enumerate(stats_glows):
                vals = [main_val, small_val, medium_val, cum_val]
                if vals[i] >= 0:
                    glow.set_alpha(0.05)
                else:
                    glow.set_alpha(0.03)

        return (
            line_main, line_main_glow, line_small, line_medium,
            line_cum, line_cum_glow,
            marker_main, glow_main, text_main,
            marker_small, glow_small, text_small,
            marker_cum, glow_cum, text_cum,
            fill_main, fill_main_neg, fill_cum
        )

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
        plt.close()
    else:
        plt.show()

    return ani


def create_sector_line_animation(sector_data=None, times=None, save_path=None, duration=12, report_type='close'):
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
    report_type: str
        'noon' - 上午场 (09:30-11:30)
        'close' - 全天场 (09:30-15:00)
    """
    if sector_data is None:
        # 使用模拟数据
        morning_times = pd.date_range(start="2026-06-18 09:30", end="2026-06-18 11:30", freq="5min")
        if report_type == 'noon':
            times = morning_times
        else:
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
        1, 2,
        width_ratios=[3.5, 1],
        wspace=0.22,
        left=0.05,
        right=0.95,
        top=0.88,
        bottom=0.10
    )

    ax_main = fig.add_subplot(gs[0])    # 主折线图
    ax_rank = fig.add_subplot(gs[1])    # 排名面板

    axes = [ax_main, ax_rank]
    _apply_dark_style(fig, axes)

    for ax in [ax_rank]:
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_linewidth(0.6)
            spine.set_color(COLORS["border"])

    # ── 专业级标题 ──────────────────────────────────────────────
    report_label = "上午场" if report_type == 'noon' else "全天场"
    fig.suptitle(
        f"行业板块资金流向对比分析 [{report_label}]",
        fontsize=20,
        fontweight="bold",
        color=COLORS["text"],
        y=0.94
    )

    fig.text(
        0.5, 0.91,
        f"数据时间: {times[0].strftime('%Y-%m-%d %H:%M')} - {times[-1].strftime('%H:%M')}  |  数据来源: 东方财富",
        fontsize=10,
        color=COLORS["text_dim"],
        ha='center'
    )

    # ── 主折线图 (专业级) ──────────────────────────────────────
    ax_main.set_xlabel("时间", fontsize=11, color=COLORS["text_secondary"])
    ax_main.set_ylabel("主力累计净流入（亿元）", fontsize=11, color=COLORS["text_secondary"])

    # 板块配色方案（从theme模块导入）
    sector_colors = SECTOR_COLORS

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
    if report_type == 'noon':
        ax_main.xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
    else:
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

    # ── 底部免责声明 ──────────────────────────────────────────
    fig.text(
        0.5, 0.02,
        "免责声明：本图表仅供参考，不构成任何投资建议。数据来源于公开市场信息，不保证其准确性和完整性。投资有风险，入市需谨慎。",
        fontsize=7,
        color=COLORS["text_muted"],
        ha='center',
        va='bottom'
    )

    # ── 动画更新函数 ──────────────────────────────────────────
    def update(frame):

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

        all_artists = list(lines.values()) + list(glows.values()) + list(markers.values())
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


def generate_all_animations(duration=12, report_type='close'):
    """
    生成所有动画

    Parameters:
    -----------
    duration: int
        动画时长（秒）
    report_type: str
        'noon' - 上午场报告（11:30触发，只含上午数据）
        'close' - 全天场报告（15:30触发，含全天数据）
    """
    print("=" * 70)
    print("资金流向动画生成器 - 专业量化风格 v2.0")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"报告类型: {'上午场' if report_type == 'noon' else '全天场'}")
    print("=" * 70)

    os.makedirs(CHART_DIR, exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")
    suffix = "_noon" if report_type == 'noon' else "_close"

    print("\n【生成个股资金流向动画】")
    for stock_code, stock_name in STOCK_LIST.items():
        print(f"\n处理: {stock_name} ({stock_code})")
        raw_data = fetch_fund_flow(stock_code)
        if raw_data:
            df = parse_fund_flow_data(raw_data)
            save_path = f"{CHART_DIR}/{stock_code}_{stock_name}_{today}{suffix}_flow.gif"
            create_stock_flow_animation(df, stock_code, stock_name, save_path, duration=duration)

    print("\n【生成板块资金流向折线图动画】")
    # 获取真实板块数据（多源自动切换）
    sector_data, times, sector_ranking_df, data_source = fetch_sector_line_data(top_n=10)

    if sector_data and times is not None:
        # 多源交叉验证
        verify_result = verify_sector_data(sector_data, sector_ranking_df, data_source)

        if not verify_result['passed']:
            print("  [!] 数据验证未通过，使用可用数据继续生成")

        # 根据报告类型过滤时间段
        if report_type == 'noon':
            # 只保留上午数据 (09:30-11:30)
            mask = (times.hour < 11) | ((times.hour == 11) & (times.minute <= 30))
            filtered_times = times[mask]
            if len(filtered_times) > 0:
                times = filtered_times
                for name in sector_data:
                    sector_data[name] = sector_data[name][:len(times)]
                print(f"  已过滤为上午场数据: {times[0].strftime('%H:%M')} ~ {times[-1].strftime('%H:%M')}")

        save_path = f"{CHART_DIR}/sector_lines_{today}{suffix}_flow.gif"
        create_sector_line_animation(
            sector_data=sector_data,
            times=times,
            save_path=save_path,
            duration=duration,
            report_type=report_type
        )
    else:
        # 降级：使用模拟数据
        print("  无法获取真实数据，使用模拟数据生成")
        save_path = f"{CHART_DIR}/sector_lines_{today}{suffix}_flow.gif"
        create_sector_line_animation(save_path=save_path, duration=duration, report_type=report_type)


if __name__ == "__main__":
    import sys
    report_type = sys.argv[1] if len(sys.argv) > 1 else 'close'
    if report_type not in ('noon', 'close'):
        print("用法: python flow_animator.py [noon|close]")
        sys.exit(1)
    generate_all_animations(duration=12, report_type=report_type)
