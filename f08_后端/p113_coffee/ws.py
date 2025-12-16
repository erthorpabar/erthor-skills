# ——————————当前文件夹路径加入搜索路径——————————
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ——————————————导入包———————————————
import json
import websocket

# ——————————————配置——————————————
HOST = "localhost"
PORT = 8188
WS_URL = f"ws://{HOST}:{PORT}/ws"
API_BASE = f"http://{HOST}:{PORT}"

# ————————————————————————————————

def ws_listen():
    ws_url = WS_URL

    def on_open(ws):
        print('ws连接已打开')

    def on_message(ws,message):
        data = json.loads(message)
        print(data)

    def on_error(ws, error):
        print("错误:", error)
        ws.close()

    def on_close(ws, close_status_code, close_msg):
        print("WebSocket连接已关闭")
    
    ws_app = websocket.WebSocketApp(ws_url,
                                    on_open=on_open,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close)
    ws_app.run_forever() # 运行ws连接

a = ws_listen()
