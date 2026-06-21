# -*- coding: utf-8 -*-
"""
定时报告生成器
在午盘(11:30)和收盘(15:30)后自动生成资金流向报告和动画
- 11:30 生成上午场报告 (09:30-11:30)
- 15:30 生成全天场报告 (09:30-15:00)
"""

import time
import traceback
from datetime import datetime, date
from flow_animator import generate_all_animations
from fund_monitor import monitor_all


def is_noon_break():
    """判断是否在午休时间（11:30-13:00）"""
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    return "11:30" <= current_time <= "13:00"


def is_after_close():
    """判断是否在收盘后（15:30之后）"""
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    return current_time >= "15:30"


def is_trading_day():
    """判断是否是交易日（周一到周五）"""
    now = datetime.now()
    return now.weekday() < 5


def wait_until(target_time_str):
    """等待到指定时间"""
    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M")

        if current_time >= target_time_str:
            return True

        target_h, target_m = map(int, target_time_str.split(':'))
        current_h, current_m = now.hour, now.minute
        wait_minutes = (target_h - current_h) * 60 + (target_m - current_m)

        if wait_minutes <= 0:
            return True

        print(f"  等待中... 当前时间: {current_time}, 目标时间: {target_time_str}")
        time.sleep(min(wait_minutes * 60, 60))


def run_report(report_type):
    """
    运行报告

    Parameters:
    -----------
    report_type: str
        'noon' - 午盘报告 (11:30触发，只含上午数据)
        'close' - 收盘报告 (15:30触发，含全天数据)
    """
    report_label = "午盘" if report_type == 'noon' else "收盘"
    print("\n" + "=" * 60)
    print(f"{report_label}资金流向报告")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"报告类型: {'上午场(09:30-11:30)' if report_type == 'noon' else '全天场(09:30-15:00)'}")
    print("=" * 60)

    # 生成数据报告
    print("\n正在生成数据报告...")
    monitor_all(show_charts=False)

    # 生成动画（传递 report_type）
    print("\n正在生成动画...")
    generate_all_animations(report_type=report_type)

    print(f"\n{report_label}报告生成完成！")


def main():
    """主函数"""
    print("=" * 60)
    print("资金流向定时报告系统")
    print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 记录当天日期，用于跨天重置标志位
    current_date = date.today()
    noon_reported = False
    close_reported = False

    while True:
        try:
            today = date.today()

            # 跨天重置标志位
            if today != current_date:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 新的一天，重置报告状态")
                current_date = today
                noon_reported = False
                close_reported = False

            # 检查是否是交易日
            if not is_trading_day():
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 今天不是交易日，等待明天...")
                time.sleep(3600)
                continue

            current_time = datetime.now().strftime("%H:%M")

            # 午盘报告 (11:30之后)
            if not noon_reported and current_time >= "11:30":
                print(f"\n[{current_time}] 到达午盘时间，生成报告...")
                try:
                    run_report('noon')
                except Exception as e:
                    print(f"[错误] 午盘报告生成失败: {e}")
                    traceback.print_exc()
                noon_reported = True

            # 收盘报告 (15:30之后)
            if not close_reported and current_time >= "15:30":
                print(f"\n[{current_time}] 到达收盘时间，生成报告...")
                try:
                    run_report('close')
                except Exception as e:
                    print(f"[错误] 收盘报告生成失败: {e}")
                    traceback.print_exc()
                close_reported = True

            # 如果两个报告都完成了，等待到第二天
            if noon_reported and close_reported:
                print(f"\n[{current_time}] 今日报告已全部生成，等待明天...")
                time.sleep(3600)
                continue

            # 等待下一次检查
            time.sleep(60)

        except KeyboardInterrupt:
            print("\n\n用户中断，定时报告系统退出。")
            break
        except Exception as e:
            print(f"\n[错误] 主循环异常: {e}")
            traceback.print_exc()
            print("  60秒后重试...")
            time.sleep(60)


if __name__ == '__main__':
    main()
