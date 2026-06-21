# -*- coding: utf-8 -*-
"""
测试动画生成功能（使用模拟数据）
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from datetime import datetime, timedelta

# 设置中文字体
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False


def generate_mock_data():
    """生成模拟数据"""
    morning_times = pd.date_range(start="2026-06-18 09:30", end="2026-06-18 11:30", freq="1min")
    afternoon_times = pd.date_range(start="2026-06-18 13:00", end="2026-06-18 15:00", freq="1min")
    all_times = morning_times.append(afternoon_times)

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


def create_stock_animation(df, stock_name="贵州茅台", stock_code="600519", save_path=None):
    """创建个股资金流向动画"""
    if df.empty:
        print(f"  {stock_name} 无数据，跳过动画生成")
        return

    df = df.copy()
    for col in ["主力净流入", "小单净流入", "中单净流入", "大单净流入", "超大单净流入"]:
        df[f"{col}(万)"] = df[col] / 10000

    df["主力累计(万)"] = df["主力净流入(万)"].cumsum()

    fig, axes = plt.subplots(2, 1, figsize=(14, 10), height_ratios=[1.2, 1])
    fig.suptitle(f"{stock_name}({stock_code}) 资金流向动画
{datetime.now().strftime("%Y-%m-%d")}",
                 fontsize=16, fontweight="bold")

    ax1 = axes[0]
    ax1.set_ylabel("净流入金额 (万元)", fontsize=12)
    ax1.set_title("分时资金净流入", fontsize=13)
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=0, color="black", linestyle="-", linewidth=0.5)

    ax2 = axes[1]
    ax2.set_ylabel("累计净流入 (万元)", fontsize=12)
    ax2.set_title("主力资金累计净流入", fontsize=13)
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color="black", linestyle="-", linewidth=0.5)

    line_main, = ax1.plot([], [], label="主力净流入", color="#FF4444", linewidth=2, alpha=0.9)
    line_small, = ax1.plot([], [], label="小单净流入", color="#4488FF", linewidth=1.5, alpha=0.7)
    line_medium, = ax1.plot([], [], label="中单净流入", color="#44BB44", linewidth=1.5, alpha=0.7)
    line_cum, = ax2.plot([], [], color="#FF8800", linewidth=2, label="主力累计净流入")

    x_min, x_max = df["time"].min(), df["time"].max()
    y_min = min(df["主力净流入(万)"].min(), df["小单净流入(万)"].min(), df["中单净流入(万)"].min()) * 1.1
    y_max = max(df["主力净流入(万)"].max(), df["小单净流入(万)"].max(), df["中单净流入(万)"].max()) * 1.1

    ax1.set_xlim(x_min, x_max)
    ax1.set_ylim(y_min, y_max)
    ax1.legend(loc="upper left", fontsize=10)
    ax1.tick_params(axis="x", rotation=30)

    cum_min = df["主力累计(万)"].min() * 1.1
    cum_max = df["主力累计(万)"].max() * 1.1
    ax2.set_xlim(x_min, x_max)
    ax2.set_ylim(cum_min, cum_max)
    ax2.legend(loc="upper left", fontsize=10)
    ax2.tick_params(axis="x", rotation=30)

    def update(frame):
        current_df = df.iloc[:frame+1]
        line_main.set_data(current_df["time"], current_df["主力净流入(万)"])
        line_small.set_data(current_df["time"], current_df["小单净流入(万)"])
        line_medium.set_data(current_df["time"], current_df["中单净流入(万)"])
        line_cum.set_data(current_df["time"], current_df["主力累计(万)"])
        return line_main, line_small, line_medium, line_cum

    frames = len(df)
    ani = animation.FuncAnimation(fig, update, frames=frames, interval=50, blit=True, repeat=False)

    plt.tight_layout()

    if save_path:
        ani.save(save_path, writer="pillow", fps=20)
        print(f"  动画已保存: {save_path}")
        plt.close()
    else:
        plt.show()

    return ani


def create_sector_animation(save_path=None, speed="slow"):
    """
    创建板块资金流向动画
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

    speed_settings = {
        "slow": {"frames": 100, "interval": 80, "fps": 10},
        "normal": {"frames": 60, "interval": 60, "fps": 15},
        "fast": {"frames": 30, "interval": 40, "fps": 25},
    }
    settings = speed_settings.get(speed, speed_settings["slow"])

    fig, ax = plt.subplots(figsize=(12, 8))

    df = df.sort_values("主力净流入(亿)", ascending=True)
    names = df["板块名称"].values
    values = df["主力净流入(亿)"].values

    colors = ["#FF4444" if v >= 0 else "#44BB44" for v in values]

    bars = ax.barh(range(len(names)), [0] * len(names), color=colors, alpha=0.8, height=0.6)

    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=10)
    ax.set_xlabel("主力净流入 (亿元)", fontsize=12)
    ax.set_title(f"行业板块 - 主力资金净流入 TOP10
{datetime.now().strftime("%Y-%m-%d")}",
                 fontsize=14, fontweight="bold")
    ax.axvline(x=0, color="black", linestyle="-", linewidth=0.5)
    ax.grid(True, axis="x", alpha=0.3)

    x_max = max(abs(values)) * 1.2
    ax.set_xlim(-x_max, x_max)

    def update(frame):
        progress = (frame + 1) / settings["frames"]
        eased_progress = 1 - (1 - progress) ** 3  # ease-out 缓动

        for i, bar in enumerate(bars):
            target_width = values[i] * eased_progress
            bar.set_width(target_width)

        return bars

    ani = animation.FuncAnimation(fig, update, frames=settings["frames"],
                                  interval=settings["interval"], blit=True, repeat=False)

    plt.tight_layout()

    if save_path:
        ani.save(save_path, writer="pillow", fps=settings["fps"])
        print(f"  动画已保存: {save_path}")
        plt.close()
    else:
        plt.show()

    return ani


if __name__ == "__main__":
    print("=" * 60)
    print("资金流向动画测试（使用模拟数据）")
    print("=" * 60)

    os.makedirs("charts", exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")

    print("
生成个股资金流向动画...")
    df = generate_mock_data()
    save_path = f"charts/test_stock_{today}_flow.gif"
    create_stock_animation(df, save_path=save_path)

    print("
生成板块资金流向动画（慢速）...")
    save_path = f"charts/test_sector_{today}_flow_slow.gif"
    create_sector_animation(save_path=save_path, speed="slow")

    print("
测试完成！请查看 charts/ 目录下的GIF文件")
