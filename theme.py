# -*- coding: utf-8 -*-
"""
专业量化主题模块 (Bloomberg Terminal 风格)
统一配色方案、字体设置、图表样式
"""

import matplotlib.pyplot as plt
import matplotlib.patheffects as pe


# ── 专业量化配色方案 ──────────────────────────────────────────
COLORS = {
    # 背景层次
    "bg":           "#0A0E14",
    "bg_secondary": "#0D1219",
    "card":         "#131A24",
    "card_hover":   "#1A2332",

    # 网格与边框
    "grid":         "#1E2A38",
    "grid_minor":   "#151D28",
    "border":       "#2A3A4E",
    "border_light": "#3A4F6A",

    # 文字层次
    "text":           "#E6EDF3",
    "text_secondary": "#B0BAC5",
    "text_dim":       "#768390",
    "text_muted":     "#545D68",

    # 金融配色
    "red":          "#FF4757",
    "red_bright":   "#FF6B81",
    "red_glow":     "#FF475740",
    "red_fill":     "#FF475718",

    "green":        "#2ED573",
    "green_bright": "#7BED9F",
    "green_glow":   "#2ED57340",
    "green_fill":   "#2ED57318",

    "blue":         "#3498DB",
    "blue_bright":  "#5DADE2",
    "blue_glow":    "#3498DB30",

    "orange":       "#F39C12",
    "orange_bright": "#F1C40F",
    "orange_glow":  "#F39C1230",

    "purple":       "#9B59B6",
    "purple_bright": "#BB8FCE",

    "cyan":         "#1ABC9C",
    "cyan_bright":  "#48C9B0",
    "cyan_glow":    "#1ABC9C30",

    "yellow":       "#F1C40F",
    "yellow_bright": "#F4D03F",

    # 特殊效果
    "glow_white":   "#FFFFFF15",
    "shadow":       "#00000040",
}

# 分时线条配色
LINE_COLORS = {
    "主力净流入":   {"main": "#FF4757", "glow": "#FF475760", "fill": "#FF475720"},
    "小单净流入":   {"main": "#3498DB", "glow": "#3498DB60", "fill": "#3498DB20"},
    "中单净流入":   {"main": "#2ED573", "glow": "#2ED57360", "fill": "#2ED57320"},
    "大单净流入":   {"main": "#9B59B6", "glow": "#9B59B660", "fill": "#9B59B620"},
    "超大单净流入": {"main": "#F39C12", "glow": "#F39C1260", "fill": "#F39C1220"},
    "累计净流入":   {"main": "#F39C12", "glow": "#F39C1260", "fill": "#F39C1220"},
}

# 板块折线配色（10个板块）
SECTOR_COLORS = [
    {"main": "#FF4757", "glow": "#FF475760"},
    {"main": "#3498DB", "glow": "#3498DB60"},
    {"main": "#2ED573", "glow": "#2ED57360"},
    {"main": "#F39C12", "glow": "#F39C1260"},
    {"main": "#9B59B6", "glow": "#9B59B660"},
    {"main": "#FF6B81", "glow": "#FF6B8160"},
    {"main": "#1ABC9C", "glow": "#1ABC9C60"},
    {"main": "#E74C3C", "glow": "#E74C3C60"},
    {"main": "#F1C40F", "glow": "#F1C40F60"},
    {"main": "#5DADE2", "glow": "#5DADE260"},
]


def setup_fonts():
    """设置中文字体"""
    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "Arial Unicode MS",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["font.weight"] = "normal"


def apply_dark_style(fig, axes):
    """应用专业深色主题到图表"""
    fig.patch.set_facecolor(COLORS["bg"])

    for ax in axes:
        ax.set_facecolor(COLORS["card"])

        ax.tick_params(
            colors=COLORS["text_dim"],
            labelsize=9,
            length=4,
            width=0.8,
            direction='out'
        )

        ax.xaxis.label.set_color(COLORS["text_secondary"])
        ax.xaxis.label.set_fontsize(11)
        ax.yaxis.label.set_color(COLORS["text_secondary"])
        ax.yaxis.label.set_fontsize(11)

        ax.title.set_color(COLORS["text"])
        ax.title.set_fontsize(13)
        ax.title.set_fontweight("bold")

        for spine in ax.spines.values():
            spine.set_color(COLORS["border"])
            spine.set_linewidth(0.8)
            spine.set_linestyle('-')

        ax.grid(True, color=COLORS["grid"], alpha=0.5, linewidth=0.6)
        ax.set_axisbelow(True)

        ax.axhline(y=0, color=COLORS["border_light"],
                   linestyle="-", linewidth=1.0, alpha=0.8)


def ease_out_cubic(t):
    """三次缓出函数"""
    return 1 - (1 - t) ** 3


# 初始化字体
setup_fonts()
