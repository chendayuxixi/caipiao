# -*- coding: utf-8 -*-
"""
板块资金流向实时监控
"""

import os
import time
from datetime import datetime
from sector_monitor import fetch_sector_list, get_sector_top
from fund_monitor import generate_chart
from config import CHART_DIR


def monitor_sector_flow(sector_type='industry', top_n=10, refresh_interval=300):
    """
    监控板块资金流向

    Parameters:
    -----------
    sector_type: str
        'industry' - 行业板块
        'concept'  - 概念板块
        'region'   - 地域板块
    top_n: int
        监控前N个板块
    refresh_interval: int
        刷新间隔（秒）
    """
    type_names = {
        'industry': '行业板块',
        'concept': '概念板块',
        'region': '地域板块',
    }

    print("=" * 60)
    print(f"板块资金流向监控 - {type_names.get(sector_type, sector_type)}")
    print(f"刷新间隔: {refresh_interval} 秒")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    while True:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 正在获取数据...")

        df = get_sector_top(sector_type, top_n)

        if not df.empty:
            print("\n" + "=" * 60)
            print(f"TOP {top_n} {type_names.get(sector_type, sector_type)} - 主力净流入排名")
            print("=" * 60)

            # 显示表格
            display_df = df[['板块名称', '涨跌幅', '主力净流入(亿)', '主力净占比',
                            '超大单净流入(亿)', '大单净流入(亿)']].copy()
            display_df.index = range(1, len(display_df) + 1)
            print(display_df.to_string())

            # 保存到CSV
            os.makedirs('data', exist_ok=True)
            today = datetime.now().strftime("%Y%m%d")
            csv_file = f"data/sector_{sector_type}_{today}.csv"
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"\n数据已保存: {csv_file}")
        else:
            print("获取数据失败，可能是非交易时间")

        print(f"\n下次刷新: {refresh_interval} 秒后")
        try:
            time.sleep(refresh_interval)
        except KeyboardInterrupt:
            print("\n\n监控已停止")
            break


def show_sector_summary():
    """显示板块资金流向汇总"""
    print("=" * 60)
    print("板块资金流向汇总")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 行业板块
    print("\n【行业板块 - 主力净流入TOP10】")
    df = get_sector_top('industry', top_n=10)
    if not df.empty:
        print(df[['板块名称', '涨跌幅', '主力净流入(亿)', '主力净占比']].to_string(index=False))

    time.sleep(1)

    # 概念板块
    print("\n【概念板块 - 主力净流入TOP10】")
    df = get_sector_top('concept', top_n=10)
    if not df.empty:
        print(df[['板块名称', '涨跌幅', '主力净流入(亿)', '主力净占比']].to_string(index=False))

    time.sleep(1)

    # 地域板块
    print("\n【地域板块 - 主力净流入TOP10】")
    df = get_sector_top('region', top_n=10)
    if not df.empty:
        print(df[['板块名称', '涨跌幅', '主力净流入(亿)', '主力净占比']].to_string(index=False))


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'realtime':
        # 实时监控模式
        sector_type = sys.argv[2] if len(sys.argv) > 2 else 'industry'
        monitor_sector_flow(sector_type, top_n=10, refresh_interval=300)
    else:
        # 单次查看模式
        show_sector_summary()
