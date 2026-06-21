# -*- coding: utf-8 -*-
"""
简单测试脚本
"""

import os
import sys

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import matplotlib
    print(f"matplotlib version: {matplotlib.__version__}")

    import matplotlib.pyplot as plt
    print("matplotlib.pyplot imported successfully")

    import matplotlib.animation as animation
    print("matplotlib.animation imported successfully")

    import numpy as np
    print(f"numpy version: {np.__version__}")

    import pandas as pd
    print(f"pandas version: {pd.__version__}")

    print("\nAll imports successful!")

    # 测试简单的动画
    print("\nTesting simple animation...")

    # 创建图表
    fig, ax = plt.subplots(figsize=(8, 6))
    x = np.linspace(0, 10, 100)
    line, = ax.plot(x, np.sin(x))

    def update(frame):
        line.set_ydata(np.sin(x + frame / 10))
        return line,

    ani = animation.FuncAnimation(fig, update, frames=50, interval=50, blit=True)

    # 保存动画
    os.makedirs("charts", exist_ok=True)
    save_path = "charts/test_simple.gif"
    ani.save(save_path, writer="pillow", fps=20)
    print(f"Simple animation saved to: {save_path}")

    plt.close()
    print("Test completed successfully!")

except ImportError as e:
    print(f"Import error: {e}")
    print("Please install required packages: pip install -r requirements.txt")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
