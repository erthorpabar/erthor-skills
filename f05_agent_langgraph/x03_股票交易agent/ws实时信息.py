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
import websocket
import uuid


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
quote = client.quote(symbol) # 获取当前价格
print(quote) # 打印当前价格
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
# 连接打开时候干什么事
def on_open(ws):
    ws.send('{"type":"subscribe","symbol":"BINANCE:BTCUSDT"}')

def on_message(ws, message):
    print(message)

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")



# 创建 WebSocket 应用
ws_url = f"wss://ws.finnhub.io?token={finnhub_api_key}"
ws_app = websocket.WebSocketApp(ws_url,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)

ws_app.on_open = on_open # 设置连接打开时的回调
ws_app.run_forever() # 运行 WebSocket 连接