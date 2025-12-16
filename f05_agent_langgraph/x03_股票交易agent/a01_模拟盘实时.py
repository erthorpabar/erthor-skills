# 将当前目录加入搜索路径
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入环境变量
from dotenv import load_dotenv
load_dotenv()

# 设置环境变量
os.environ["LLM_URL"] = "https://open.bigmodel.cn/api/paas/v4/"
os.environ["LLM_API_KEY"] = "bcb4b79cf63d81bb74004a7438afe404.ZWtkkACpqBa522oQ"
os.environ["LLM_MODEL"] = "GLM-4-Flash-250414"
os.environ["FINNHUB_API_KEY"] = "d4u6u71r01qu53ud68kgd4u6u71r01qu53ud68l0"


api_url = os.getenv("LLM_URL")
api_key = os.getenv("LLM_API_KEY")
model = os.getenv("LLM_MODEL")
finnhub_api_key = os.getenv("FINNHUB_API_KEY")


# 导入包
import finnhub
''' 
网址
https://finnhub.io/
'''
import time
from datetime import datetime, timedelta

# ——————————————公共数据——————————————————
symbol = 'BINANCE:BTCUSDT' # 交易物代码
trade_interval = 60 # 交易周期

ori_capital = 100000.0 # 初始金额
capital = ori_capital # 当前可用资金

in_ratio = 0.30 # 投资比例 
commission_rate = 0.001  # 手续费率 (已考虑滑点)

all_trades = [] # 用于存储所有交易记录的列表


# ————————————————————————————————————————
client = finnhub.Client(api_key=finnhub_api_key) # 创建 Finnhub 客户端


# 
# quote = client.quote(symbol) # 获取当前价格
# print(quote) # 打印当前价格
'''
{
  'c': 175.84,    # 当前价格 (current)
  'd': -0.62,     # 涨跌额 (change)
  'dp': -0.3512,  # 涨跌幅% (change percent)
  'h': 177.49,    # 当日最高价 (high)
  'l': 175.36,    # 当日最低价 (low)
  'o': 177.35,    # 开盘价 (open)
  'pc': 176.46,   # 前收盘价 (previous close)
  't': 1702401600 # 时间戳 (timestamp)
}
'''

# ——————————————————————————————————————————————
# 获取历史三周期k线 分钟级别
# 计算时间范围：获取最近3个周期的分钟K线数据
# end_time = int(time.time())  # 当前时间戳（秒）
# start_time = end_time - (3 * trade_interval * 60)  # 往前推3个周期

# 加密货币使用 crypto_candles，而不是 stock_candles
# resolution: '1' 表示1分钟K线
# candles = client.crypto_candles(symbol, '1', start_time, end_time)
# print("历史K线数据:", candles)
'''
返回格式:
{
  'c': [97500.5, 97510.2, ...],  # 收盘价数组 (close)
  'h': [97550.0, 97560.0, ...],  # 最高价数组 (high)
  'l': [97480.0, 97490.0, ...],  # 最低价数组 (low)
  'o': [97490.0, 97500.0, ...],  # 开盘价数组 (open)
  's': 'ok',                      # 状态 (status)
  't': [1702401600, 1702401660, ...],  # 时间戳数组（秒）
  'v': [10.5, 12.3, ...]          # 成交量数组 (volume)
}
'''

# print(client.crypto_candles('BINANCE:BTCUSDT', 'D', 1590988249, 1591852249))
