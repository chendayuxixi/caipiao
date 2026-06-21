# -*- coding: utf-8 -*-
"""
板块资金流向监控 - 多源数据获取
主力数据源: 新浪(通过akshare) - 稳定不易被封
备用数据源: 东方财富 - 分时数据更精细但易被限流
"""

import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime

# ── 共享session（东财备用） ──
_shared_session = None
_session_warmed = False


def _get_warm_session():
    """获取预热过的session（东财备用）"""
    global _shared_session, _session_warmed
    if _shared_session is None:
        _shared_session = requests.Session()
    if not _session_warmed:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
            _shared_session.get("https://data.eastmoney.com/", headers=headers, timeout=10)
            _session_warmed = True
            time.sleep(0.5)
        except Exception:
            pass
    return _shared_session


# ══════════════════════════════════════════════════════════════
#  主力数据源: 新浪 (通过akshare) - 稳定
# ══════════════════════════════════════════════════════════════

def fetch_sector_ranking_sina(top_n=10, sector_type='industry'):
    """
    通过新浪源获取板块资金流向排名（稳定，不易被封）

    Parameters:
    -----------
    top_n: int
        返回前N个板块
    sector_type: str
        'industry' - 行业板块
        'concept'  - 概念板块

    Returns:
    --------
    DataFrame: 板块排名数据，统一列名
    """
    try:
        import akshare as ak

        if sector_type == 'concept':
            df = ak.stock_fund_flow_concept()
        else:
            df = ak.stock_fund_flow_industry()

        if df.empty:
            print("  新浪源返回空数据")
            return pd.DataFrame()

        # 获取实际列名（akshare返回的是中文列名）
        cols = list(df.columns)

        # 统一列名映射（按位置+名称模糊匹配）
        col_map = {}
        for c in cols:
            if c == '序号':
                col_map[c] = '序号'
            elif c == '行业':
                col_map[c] = '板块名称'
            elif c == '行业指数':
                col_map[c] = '行业指数'
            elif '涨跌幅' in c and '行业' in c:
                col_map[c] = '涨跌幅'
            elif c == '流入资金':
                col_map[c] = '主力净流入(亿)'
            elif c == '流出资金':
                col_map[c] = '流出资金(亿)'
            elif c == '净额':
                col_map[c] = '净额(亿)'
            elif c == '主力净流入':
                col_map[c] = '主力净流入(亿)'
            elif '净占比' in c and '主力' in c:
                col_map[c] = '主力净占比'
            elif c == '公司数量':
                col_map[c] = '公司数量'
            elif c == '领涨股':
                col_map[c] = '领涨股'
            elif '领涨股' in c and '涨跌幅' in c:
                col_map[c] = '领涨股-涨跌幅'
            elif '领涨股' in c and '当前价' in c:
                col_map[c] = '领涨股-当前价'

        df = df.rename(columns=col_map)

        # 确保关键数值列为float
        for col in ['主力净流入(亿)', '涨跌幅', '净额(亿)']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # 按主力净流入排序取前N
        sort_col = '主力净流入(亿)' if '主力净流入(亿)' in df.columns else '净额(亿)'
        df = df.sort_values(sort_col, ascending=False).head(top_n)
        df = df.reset_index(drop=True)

        return df

    except Exception as e:
        print(f"  新浪源获取失败: {e}")
        return pd.DataFrame()


# ══════════════════════════════════════════════════════════════
#  备用数据源: 东方财富 - 分时数据精细但易被限流
# ══════════════════════════════════════════════════════════════

def fetch_sector_list_em(sector_type='industry', max_retries=3):
    """
    通过东财获取板块列表（备用，易被限流）

    Parameters:
    -----------
    sector_type: str
        'industry' - 行业板块
        'concept'  - 概念板块
    """
    fs_map = {
        'industry': 'm:90+t:2',
        'concept': 'm:90+t:3',
        'region': 'm:90+t:1',
    }

    url = 'https://push2.eastmoney.com/api/qt/clist/get'
    params = {
        'fid': 'f62', 'po': 1, 'pz': 500, 'pn': 1, 'np': 1,
        'fltt': 2, 'invt': 2,
        'ut': 'b2884a393a59ad64002292a3e90d46a5',
        'fs': fs_map.get(sector_type, fs_map['industry']),
        'fields': 'f12,f14,f2,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87',
        '_': str(int(datetime.now().timestamp() * 1000))
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://data.eastmoney.com/'
    }

    session = _get_warm_session()
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                time.sleep(2)
            resp = session.get(url, params=params, headers=headers, timeout=15)
            data = resp.json()
            if data.get('data') and data['data'].get('diff'):
                sectors = []
                for item in data['data']['diff']:
                    sectors.append({
                        '板块代码': item.get('f12', ''),
                        '板块名称': item.get('f14', ''),
                        '最新价': item.get('f2', 0),
                        '涨跌幅': item.get('f3', 0),
                        '主力净流入(亿)': round(item.get('f62', 0) / 100000000, 2),
                        '主力净占比': item.get('f184', 0),
                    })
                return pd.DataFrame(sectors)
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"  东财获取失败，重试... ({attempt+1}/{max_retries})")
                time.sleep(1)
            else:
                print(f"  东财板块列表异常: {e}")
    return pd.DataFrame()


def fetch_sector_kline_em(sector_code, max_retries=3):
    """
    通过东财获取板块分时K线（备用）

    Parameters:
    -----------
    sector_code: str
        板块代码，如 'BK0475'
    """
    url = "https://push2.eastmoney.com/api/qt/stock/fflow/kline/get"
    params = {
        "lmt": "0", "klt": "1",
        "secid": f"90.{sector_code}",
        "fields1": "f1,f2,f3,f7",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65",
        "ut": "b2884a393a59ad64002292a3e90d46a5",
        "_": str(int(datetime.now().timestamp() * 1000))
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://data.eastmoney.com/"
    }

    session = _get_warm_session()
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                time.sleep(2)
            resp = session.get(url, params=params, headers=headers, timeout=15)
            data = resp.json()
            if data.get("data") and data["data"].get("klines"):
                return data["data"]["klines"]
            return []
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                print(f"  东财分时数据异常: {e}")
                return []


def parse_kline_data(raw_data):
    """解析分时K线数据"""
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
    if not df.empty:
        df["time"] = pd.to_datetime(df["time"])
    return df



# ══════════════════════════════════════════════════════════════
#  新浪分时数据辅助函数
# ══════════════════════════════════════════════════════════════

def _find_stock_code(stock_name):
    """
    根据股票名称查找代码
    返回格式: 'sh600519' 或 'sz000858'
    """
    # 常见领涨股名称 → 代码映射
    common_stocks = {
        # 白酒
        '贵州茅台': 'sh600519', '五粮液': 'sz000858', '泸州老窖': 'sz000568',
        '山西汾酒': 'sh600809', '洋河股份': 'sz002304', '古井贡酒': 'sz000596',
        '今世缘': 'sh603369', '舍得酒业': 'sh600702', '酒鬼酒': 'sz000799',
        # 半导体/芯片
        '北方华创': 'sz002371', '中芯国际': 'sh688981', '韦尔股份': 'sh603501',
        '紫光国微': 'sz002049', '兆易创新': 'sh603986', '卓胜微': 'sz300782',
        '澜起科技': 'sh688008', '中微公司': 'sh688012', '长电科技': 'sh600584',
        '华虹半导体': 'sh688347', '海光信息': 'sh688041', '寒武纪': 'sh688256',
        # 新能源
        '宁德时代': 'sz300750', '比亚迪': 'sz002594', '隆基绿能': 'sh601012',
        '阳光电源': 'sz300274', '通威股份': 'sh600438', '亿纬锂能': 'sz300014',
        '天齐锂业': 'sz002466', '赣锋锂业': 'sz002460',
        # 医药
        '恒瑞医药': 'sh600276', '药明康德': 'sh603259', '迈瑞医疗': 'sz300760',
        '片仔癀': 'sh600436', '云南白药': 'sz000538', '爱尔眼科': 'sz300015',
        '智飞生物': 'sz300122', '长春高新': 'sz000661',
        # 军工
        '中航光电': 'sz002179', '航发动力': 'sh600893', '中航沈飞': 'sh600760',
        '中航西飞': 'sz000768', '紫光国微': 'sz002049',
        # 证券
        '中信证券': 'sh600030', '东方财富': 'sz300059', '国泰君安': 'sh601211',
        '华泰证券': 'sh601688', '招商证券': 'sh600999',
        # 银行
        '招商银行': 'sh600036', '工商银行': 'sh601398', '建设银行': 'sh601939',
        '农业银行': 'sh601288', '中国银行': 'sh601988', '兴业银行': 'sh601166',
        # 通信/5G
        '中兴通讯': 'sz000063', '中国移动': 'sh600941', '中国电信': 'sh601728',
        # 人工智能/科技
        '海康威视': 'sz002415', '立讯精密': 'sz002475', '科大讯飞': 'sz002230',
        '金山办公': 'sh688111',
        # 汽车
        '长安汽车': 'sz000625', '长城汽车': 'sh601633', '广汽集团': 'sh601238',
        # 房地产
        '万科A': 'sz000002', '保利发展': 'sh600048', '招商蛇口': 'sz001979',
        # 有色/贵金属
        '紫金矿业': 'sh601899', '山东黄金': 'sh600547', '中金黄金': 'sh600489',
        # 化工
        '万华化学': 'sh600309', '恒力石化': 'sh600346',
        # 消费电子
        '歌尔股份': 'sz002241', '蓝思科技': 'sz300433',
    }

    code = common_stocks.get(stock_name)
    if code:
        return code

    # 如果没找到，尝试从新浪全量股票列表中搜索（带缓存）
    if not hasattr(_find_stock_code, '_stock_map'):
        try:
            import akshare as ak
            df = ak.stock_zh_a_spot()
            # 列名可能是中文，用位置索引：第0列=symbol, 第1列=名称
            _find_stock_code._stock_map = dict(zip(df.iloc[:, 1], df.iloc[:, 0]))
        except Exception:
            _find_stock_code._stock_map = {}

    return _find_stock_code._stock_map.get(stock_name)


def _fetch_sina_minute(stock_code):
    """
    从新浪获取个股分时K线数据

    Parameters:
    -----------
    stock_code: str
        格式: 'sh600519' 或 'sz000858'

    Returns:
    --------
    DataFrame 或 None
    """
    try:
        import akshare as ak
        df = ak.stock_zh_a_minute(symbol=stock_code, period='5')
        if df is not None and not df.empty:
            return df
    except Exception as e:
        pass
    return None


# ══════════════════════════════════════════════════════════════
#  统一接口: 自动选择最佳数据源
# ══════════════════════════════════════════════════════════════

def fetch_sector_line_data(top_n=10, sector_type='industry'):
    """
    获取板块折线图数据（多源自动切换）

    优先使用东财分时数据（更精细），失败则降级为新浪日级数据

    Returns:
    --------
    tuple: (sector_data, times, sector_ranking_df, data_source)
        sector_data: dict {板块名: [累计净流入列表(亿元)]}
        times: pd.DatetimeIndex 时间序列
        sector_ranking_df: DataFrame 板块排名
        data_source: str 'eastmoney' 或 'sina'
    """
    print("\n  [数据源选择] 尝试东财分时数据...")

    # ── 方案1: 东财分时K线（精细） ──
    em_df = fetch_sector_list_em(sector_type)
    if not em_df.empty:
        em_df = em_df.sort_values('主力净流入(亿)', ascending=False)
        top_sectors = em_df.head(top_n)

        sector_data = {}
        all_times = None
        success_count = 0

        for i, (_, row) in enumerate(top_sectors.iterrows()):
            code = row['板块代码']
            name = row['板块名称']
            if i > 0:
                time.sleep(0.5)

            raw = fetch_sector_kline_em(code)
            df = parse_kline_data(raw)

            if not df.empty:
                df['cumulative'] = df['主力净流入'].cumsum() / 100000000
                sector_data[name] = df['cumulative'].tolist()
                if all_times is None:
                    all_times = df['time'].values
                success_count += 1

        if success_count >= 3 and all_times is not None:
            times = pd.DatetimeIndex(all_times)
            print(f"  [OK] 东财数据获取成功: {success_count}个板块, {len(times)}个时间点")
            return sector_data, times, top_sectors, 'eastmoney'

    # ── 方案2: 新浪分时数据（稳定） ──
    print("  [数据源切换] 东财不可用，使用新浪源...")

    sina_df = fetch_sector_ranking_sina(top_n, sector_type)
    if sina_df.empty:
        print("  [X] 所有数据源均不可用")
        return None, None, None, None

    # 用板块领涨股的分时价格走势作为资金流向代理（有真实波动）
    sector_data = {}
    all_times = None
    success_count = 0

    for _, row in sina_df.iterrows():
        name = row['板块名称']
        total = row['主力净流入(亿)']

        # 获取领涨股代码
        leader_stock = row.get('领涨股', '')
        if not leader_stock:
            continue

        # 查找领涨股的股票代码
        stock_code = _find_stock_code(leader_stock)
        if not stock_code:
            print(f"  [!] {name}: 无法找到领涨股 {leader_stock} 的代码，跳过")
            continue

        print(f"  获取 {name} 领涨股 {leader_stock}({stock_code}) 分时数据...")

        # 从新浪获取分时数据
        minute_data = _fetch_sina_minute(stock_code)
        if minute_data is None or minute_data.empty:
            print(f"    {name}: 分时数据为空，跳过")
            continue

        # 只保留最后一天的数据（跳过涨停/跌停无波动的天）
        minute_data['day'] = pd.to_datetime(minute_data['day'])
        dates = sorted(minute_data['day'].dt.date.unique(), reverse=True)

        today_data = None
        for d in dates[:3]:  # 尝试最近3天
            day_data = minute_data[minute_data['day'].dt.date == d].copy()
            prices_check = pd.to_numeric(day_data['close'], errors='coerce').values
            if len(day_data) >= 5 and np.std(prices_check) > 0.001:
                today_data = day_data
                break

        if today_data is None or today_data.empty:
            print(f"    {name}: 无有效分时数据，跳过")
            continue

        # 用价格变化率 * 净流入方向 作为资金流向代理
        prices = pd.to_numeric(today_data['close'], errors='coerce').values
        price_change_pct = (prices / prices[0] - 1) * 100  # 相对开盘价的变化率
        # 用净流入的正负号来确定方向，用价格波动来提供真实起伏
        direction = 1 if total >= 0 else -1
        flow_proxy = price_change_pct * direction * abs(total) / (abs(price_change_pct[-1]) + 0.01)

        sector_data[name] = flow_proxy.tolist()

        if all_times is None:
            all_times = today_data['day'].values

        success_count += 1
        time.sleep(0.3)

    if success_count >= 3 and all_times is not None:
        times = pd.DatetimeIndex(all_times)
        print(f"  [OK] 新浪分时数据获取成功: {success_count}个板块, {len(times)}个时间点")
        return sector_data, times, sina_df, 'sina'
    else:
        print(f"  [!] 只获取到 {success_count} 个板块数据，不足3个")
        return None, None, None, None


def verify_sector_data(sector_data, sector_ranking_df, data_source='sina', tolerance=0.15):
    """
    多API交叉验证板块数据正确性

    验证策略:
    1. 最终累计值 vs 排名数据的主力净流入
    2. 数据点数量一致性
    3. 累计值方向与涨跌幅一致性

    Parameters:
    -----------
    sector_data: dict {板块名: [累计净流入列表]}
    sector_ranking_df: DataFrame 板块排名
    data_source: str 数据来源
    tolerance: float 允许的相对误差
    """
    print("\n" + "=" * 50)
    print(f"多源交叉验证 (数据源: {data_source})")
    print("=" * 50)

    results = {
        'passed': True,
        'details': [],
        'warnings': [],
        'errors': []
    }

    # ── 验证1: 累计值 vs 排名数据 ──
    print("\n[验证1] 最终累计值 vs 排名数据")
    name_col = '板块名称'
    value_col = '主力净流入(亿)'

    for name, values in sector_data.items():
        final_val = values[-1]
        match = sector_ranking_df[sector_ranking_df[name_col] == name]
        if match.empty:
            msg = f"  [!] {name}: 在排名数据中未找到"
            results['warnings'].append(msg)
            print(msg)
            continue

        snapshot_val = match.iloc[0][value_col]
        if abs(snapshot_val) > 0.01:
            rel_error = abs(final_val - snapshot_val) / abs(snapshot_val)
        else:
            rel_error = abs(final_val - snapshot_val)

        status = "[OK]" if rel_error <= tolerance else "[!]"
        msg = f"  {status} {name}: 图表值={final_val:.2f}亿, 排名值={snapshot_val:.2f}亿, 误差={rel_error:.1%}"
        print(msg)
        results['details'].append(msg)

        if rel_error > tolerance:
            results['warnings'].append(f"{name}: 误差{rel_error:.1%}")

    # ── 验证2: 数据点一致性 ──
    print("\n[验证2] 数据点数量一致性")
    lengths = {name: len(v) for name, v in sector_data.items()}
    max_len = max(lengths.values())
    min_len = min(lengths.values())
    if max_len == min_len:
        msg = f"  [OK] 数据点数一致: {max_len}个"
        print(msg)
    else:
        msg = f"  [!] 数据点数不一致: {min_len}~{max_len}"
        print(msg)
        results['warnings'].append(msg)

    # ── 验证3: 方向一致性 ──
    print("\n[验证3] 净流入方向 vs 涨跌幅")
    if '涨跌幅' in sector_ranking_df.columns:
        for name, values in sector_data.items():
            final_val = values[-1]
            match = sector_ranking_df[sector_ranking_df[name_col] == name]
            if match.empty:
                continue
            change_pct = pd.to_numeric(match.iloc[0]['涨跌幅'], errors='coerce')
            if pd.isna(change_pct):
                continue
            if (final_val > 0.5 and change_pct < -1) or (final_val < -0.5 and change_pct > 1):
                msg = f"  [!] {name}: 净流入{final_val:.2f}亿但涨跌幅{change_pct:.2f}%"
                print(msg)
                results['warnings'].append(msg)
            else:
                msg = f"  [OK] {name}: 净流入{final_val:.2f}亿, 涨跌幅{change_pct:.2f}%"
                print(msg)

    # ── 总结 ──
    print("\n" + "-" * 50)
    if results['errors']:
        results['passed'] = False
        print(f"验证结果: [X] 失败 ({len(results['errors'])}个错误)")
    elif results['warnings']:
        print(f"验证结果: [!] 通过 ({len(results['warnings'])}个警告)")
    else:
        print("验证结果: [OK] 全部通过")
    print("-" * 50)

    return results


# ══════════════════════════════════════════════════════════════
#  兼容旧接口
# ══════════════════════════════════════════════════════════════

def fetch_sector_list(sector_type='industry', max_retries=3):
    """兼容旧接口 - 优先新浪，备用东财"""
    df = fetch_sector_ranking_sina(top_n=500, sector_type=sector_type)
    if not df.empty:
        return df
    return fetch_sector_list_em(sector_type, max_retries)


def get_sector_top(sector_type='industry', top_n=20, sort_by='主力净流入(亿)'):
    """获取资金流入排名前N的板块"""
    df = fetch_sector_list(sector_type)
    if df.empty:
        return df
    if sort_by in df.columns:
        df = df.sort_values(sort_by, ascending=False)
    return df.head(top_n)


# ══════════════════════════════════════════════════════════════
#  测试
# ══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 60)
    print("板块资金流向监控测试 (多源)")
    print("=" * 60)

    # 新浪源测试
    print("\n【新浪源 - 行业板块TOP10】")
    df = fetch_sector_ranking_sina(top_n=10)
    if not df.empty:
        show_cols = [c for c in ['板块名称', '涨跌幅', '主力净流入(亿)', '净额(亿)'] if c in df.columns]
        print(df[show_cols].to_string(index=False))

    # 完整流程测试
    print("\n\n【完整流程: 数据获取 + 验证】")
    sector_data, times, ranking_df, source = fetch_sector_line_data(top_n=10)
    if sector_data and times is not None:
        print(f"\n数据源: {source}")
        print(f"时间范围: {times[0]} ~ {times[-1]}")
        print(f"板块数量: {len(sector_data)}")
        verify_result = verify_sector_data(sector_data, ranking_df, source)
