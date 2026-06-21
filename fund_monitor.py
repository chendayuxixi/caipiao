# -*- coding: utf-8 -*-
"""
股票资金流向监控工具
功能：获取分时资金流向数据，生成曲线图
"""

import os
import json
import time
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from config import STOCK_LIST, DATA_DIR, CHART_DIR

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


def fetch_fund_flow(stock_code, max_retries=3):
    """
    获取股票分时资金流向数据
    数据来源：东方财富
    """
    if stock_code.startswith(('6', '9')):
        secid = f"1.{stock_code}"
    else:
        secid = f"0.{stock_code}"
    
    url = "https://push2.eastmoney.com/api/qt/stock/fflow/kline/get"
    
    params = {
        "lmt": "0",
        "klt": "1",
        "secid": secid,
        "fields1": "f1,f2,f3,f7",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65",
        "ut": "b2884a393a59ad64002292a3e90d46a5",
        "_": str(int(datetime.now().timestamp() * 1000))
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://quote.eastmoney.com/"
    }
    
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            data = resp.json()
            
            if data.get("data") and data["data"].get("klines"):
                return data["data"]["klines"]
            else:
                print(f"  获取数据为空，可能是非交易时间")
                return []
                
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"  获取失败，重试中... ({attempt+1}/{max_retries})")
                time.sleep(1)
            else:
                print(f"  获取数据失败: {e}")
                return []
    
    return []


def parse_fund_flow_data(raw_data):
    """
    解析资金流向数据
    """
    if not raw_data:
        return pd.DataFrame()
    
    records = []
    for line in raw_data:
        parts = line.split(",")
        if len(parts) >= 6:
            records.append({
                "time": parts[0],
                "主力净流入": float(parts[1]),
                "小单净流入": float(parts[2]),
                "中单净流入": float(parts[3]),
                "大单净流入": float(parts[4]),
                "超大单净流入": float(parts[5]),
            })
    
    df = pd.DataFrame(records)
    df["time"] = pd.to_datetime(df["time"])
    return df


def save_data(df, stock_code, stock_name):
    """保存数据到CSV"""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    today = datetime.now().strftime("%Y%m%d")
    filename = f"{DATA_DIR}/{stock_code}_{stock_name}_{today}.csv"
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"  数据已保存: {filename}")
    return filename


def generate_chart(df, stock_code, stock_name, show=True):
    """
    生成资金流向曲线图
    """
    if df.empty:
        print(f"  无数据，跳过图表生成")
        return
    
    os.makedirs(CHART_DIR, exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")
    
    # 转换为万元
    df = df.copy()
    for col in ["主力净流入", "小单净流入", "中单净流入", "大单净流入", "超大单净流入"]:
        df[f"{col}(万)"] = df[col] / 10000
    
    # 计算累计值
    df["主力累计(万)"] = df["主力净流入(万)"].cumsum()
    
    # 创建图表
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), height_ratios=[1.2, 1])
    fig.suptitle(f"{stock_name}({stock_code}) 资金流向分析\n{today}", fontsize=16, fontweight='bold')
    
    # ========== 子图1: 分时资金净流入曲线 ==========
    ax1 = axes[0]
    
    ax1.plot(df["time"], df["主力净流入(万)"], 
             label="主力净流入", color="#FF4444", linewidth=2, alpha=0.9)
    ax1.plot(df["time"], df["小单净流入(万)"], 
             label="小单净流入", color="#4488FF", linewidth=1.5, alpha=0.7)
    ax1.plot(df["time"], df["中单净流入(万)"], 
             label="中单净流入", color="#44BB44", linewidth=1.5, alpha=0.7)
    
    # 填充区域
    ax1.fill_between(df["time"], df["主力净流入(万)"], 0, 
                     where=(df["主力净流入(万)"] >= 0), 
                     color="#FF4444", alpha=0.15, label="")
    ax1.fill_between(df["time"], df["主力净流入(万)"], 0, 
                     where=(df["主力净流入(万)"] < 0), 
                     color="#44BB44", alpha=0.15, label="")
    
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax1.set_ylabel("净流入金额 (万元)", fontsize=12)
    ax1.set_title("分时资金净流入", fontsize=13)
    ax1.legend(loc="upper left", fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='x', rotation=30)
    
    # ========== 子图2: 主力累计净流入 ==========
    ax2 = axes[1]
    
    colors = ["#FF4444" if v >= 0 else "#44BB44" for v in df["主力累计(万)"]]
    ax2.bar(df["time"], df["主力累计(万)"], 
            color=colors, alpha=0.7, width=0.0005)
    ax2.plot(df["time"], df["主力累计(万)"], 
             color="#FF8800", linewidth=2, label="主力累计净流入")
    
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax2.set_ylabel("累计净流入 (万元)", fontsize=12)
    ax2.set_title("主力资金累计净流入", fontsize=13)
    ax2.legend(loc="upper left", fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(axis='x', rotation=30)
    
    plt.tight_layout()
    
    # 保存图表
    chart_file = f"{CHART_DIR}/{stock_code}_{stock_name}_{today}.png"
    plt.savefig(chart_file, dpi=150, bbox_inches='tight')
    print(f"  图表已保存: {chart_file}")
    
    if show:
        plt.show()
    else:
        plt.close()
    
    return chart_file


def monitor_single_stock(stock_code, stock_name, show_chart=True):
    """监探单只股票"""
    print(f"\n{'='*50}")
    print(f"监控股票: {stock_name} ({stock_code})")
    print(f"{'='*50}")
    
    # 获取数据
    print("正在获取资金流向数据...")
    raw_data = fetch_fund_flow(stock_code)
    
    if not raw_data:
        print("未获取到数据，请在交易时间运行")
        return None
    
    # 解析数据
    df = parse_fund_flow_data(raw_data)
    print(f"获取到 {len(df)} 条分钟数据")
    
    # 保存数据
    save_data(df, stock_code, stock_name)
    
    # 生成图表
    print("正在生成图表...")
    generate_chart(df, stock_code, stock_name, show=show_chart)
    
    return df


def monitor_all(show_charts=True):
    """监控所有股票"""
    print("=" * 60)
    print("股票资金流向监控工具")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    all_data = {}
    
    for stock_code, stock_name in STOCK_LIST.items():
        df = monitor_single_stock(stock_code, stock_name, show_chart=show_charts)
        if df is not None:
            all_data[stock_code] = {
                "name": stock_name,
                "data": df,
                "summary": {
                    "主力净流入(万)": round(df["主力净流入"].sum() / 10000, 2),
                    "小单净流入(万)": round(df["小单净流入"].sum() / 10000, 2),
                    "中单净流入(万)": round(df["中单净流入"].sum() / 10000, 2),
                    "大单净流入(万)": round(df["大单净流入"].sum() / 10000, 2),
                    "超大单净流入(万)": round(df["超大单净流入"].sum() / 10000, 2),
                }
            }
        # 添加延迟避免请求过快
        time.sleep(0.5)
    
    # 打印汇总
    if all_data:
        print("\n" + "=" * 60)
        print("今日资金流向汇总")
        print("=" * 60)
        for code, info in all_data.items():
            print(f"\n{info['name']} ({code}):")
            for k, v in info["summary"].items():
                print(f"  {k}: {v:>12.2f} 万")
    
    return all_data


if __name__ == "__main__":
    monitor_all()
