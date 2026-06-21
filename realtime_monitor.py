# -*- coding: utf-8 -*-
"""
实时资金流向监控（交易时间内自动刷新）
"""

import time
from datetime import datetime
from fund_monitor import fetch_fund_flow, parse_fund_flow_data, generate_chart
from config import STOCK_LIST


def is_trading_time():
    """判断是否在交易时间"""
    now = datetime.now()
    weekday = now.weekday()

    if weekday >= 5:
        return False

    current_time = now.strftime("%H:%M")

    # 上午 9:30-11:30, 下午 13:00-15:00
    return ("09:30" <= current_time <= "11:30" or
            "13:00" <= current_time <= "15:00")


def realtime_monitor(stock_code, stock_name, refresh_interval=60):
    """
    实时监控单只股票
    refresh_interval: 刷新间隔（秒）
    """
    print(f"开始实时监控: {stock_name} ({stock_code})")
    print(f"刷新间隔: {refresh_interval} 秒")
    print("按 Ctrl+C 停止监控\n")

    last_chart_minute = -1  # 记录上次生成图表的分钟，避免重复

    try:
        while True:
            if not is_trading_time():
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 非交易时间，等待中...")
                time.sleep(60)
                continue

            print(f"[{datetime.now().strftime('%H:%M:%S')}] 正在获取数据...")

            raw_data = fetch_fund_flow(stock_code)
            if raw_data:
                df = parse_fund_flow_data(raw_data)
                if not df.empty:
                    latest = df.iloc[-1]
                    total_main = df["主力净流入"].sum() / 10000
                    print(f"  最新主力净流入: {latest['主力净流入']/10000:.2f} 万")
                    print(f"  累计主力净流入: {total_main:.2f} 万")

                    # 每5分钟更新一次图表（不阻塞）
                    current_minute = datetime.now().minute
                    if current_minute % 5 == 0 and current_minute != last_chart_minute:
                        generate_chart(df, stock_code, stock_name, show=False)
                        last_chart_minute = current_minute

            time.sleep(refresh_interval)

    except KeyboardInterrupt:
        print("\n\n实时监控已停止。")


if __name__ == "__main__":
    stock_code = list(STOCK_LIST.keys())[0]
    stock_name = STOCK_LIST[stock_code]
    realtime_monitor(stock_code, stock_name, refresh_interval=60)
