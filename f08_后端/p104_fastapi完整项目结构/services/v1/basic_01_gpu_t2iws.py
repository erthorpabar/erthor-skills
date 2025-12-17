"""ws 提交生成任务"""
# 导入包
import requests
import json
import random

import websocket
import uuid

# 配置
from core.config import settings


def generate_image(prompt, width, height):
    
    url = settings.COMFYUI_API_URL
    # url = "http://61.49.53.9:6017" # 测试打开
    client_id = str(uuid.uuid4())  # 客户端ID
    ws_url = f"ws://{url.replace('http://', '')}/ws?clientId={client_id}"  # 替换 http://

    prompt_id = None
    start_time = None
    finish_time = None
    img_name_list = [] # 文件名称
    img_url_list = [] # 根据文件名称索引到网址
    result = {}

    node = None # 当前执行节点

    def on_open(ws): # 在打开的时候提交生成任务
        print("WebSocket连接已打开")
        nonlocal prompt_id
        try:
            # 打开工作流文件
            with open('services/comfyui_api/flux_t2i_api.json', 'r',encoding='utf-8') as f:
                work_flow = json.load(f)

            # 修改参数
            work_flow['26']['inputs']['noise_seed'] = random.randint(0, 4294967295) # 设置随机种子
            work_flow['24']['inputs']['steps'] = 20 # 步数
            work_flow['35']['inputs']['input_str'] = prompt # 输入提示词
            work_flow['36']['inputs']['input_int'] = width # 宽度
            work_flow['37']['inputs']['input_int'] = height # 高度


            # 提交生成任务
            response = requests.post(
                url=f'{url}/prompt',
                json={"prompt": work_flow,
                      "client_id": client_id},
                timeout=10  # 设置请求超时时间
            )

            # 获取prompt_id 
            prompt_id = response.json().get('prompt_id')
        except requests.RequestException as e:
            print(f"提交作图失败: {e}")
            ws.close()  # 关闭连接

    
    def on_message(ws, message):
        # 可以在嵌套函数中修改上级函数的变量
        nonlocal result, start_time, finish_time, prompt_id, img_name_list, img_url_list, node

        # 解析信息
        data = json.loads(message)
        print(data) # 测试，每次都打印消息变化

        # ——————————判断生图阶段——————————
        if data['type'] == 'status': # 任务数量变化
            # print('总任务数量：', data['data']['status']['exec_info']['queue_remaining'])
            pass

        elif data['type'] == 'execution_start': # 任务开始
            start_time = data['data']['timestamp']
            prompt_id = data['data']['prompt_id']

        elif data['type'] == 'execution_cached': # 缓存，不知道有什么用
            prompt_id = data['data']['prompt_id']

        elif data['type'] == 'executing': # 正在执行，某个节点中
            prompt_id = data['data']['prompt_id']
            node = data['data']['node']
        
        elif data['type'] == 'progress': # 生成进度
            prompt_id = data['data']['prompt_id']
            print(f"node[{node}]:", data['data']['value'], "/", data['data']['max'])

        elif data['type'] == 'executed': # 执行完成
            prompt_id = data['data']['prompt_id']
            # if (
            #     data['data']['output'] is not None and # 有output
            #    'images' in data['data']['output'] and  # 有些output中没有image
            #    data['data']['output']['images'] is not None): # 有些会输出none
            #    img_name_list.append(data['data']['output']['images'][0]['filename']) # 获取图片名称
            try:
               if data['data']['output']['images'][0]['type'] == 'output':  # 只保存最终输出的图片
                   img_name_list.append(data['data']['output']['images'][0]['filename'])
            except (KeyError, TypeError, IndexError):
               pass  # 忽略没有图片输出的节点
        elif data['type'] == 'execution_success': # 执行成功，获取图片url或content
            prompt_id = data['data']['prompt_id']
            finish_time = data['data']['timestamp']

            img_name_list = list(set(img_name_list)) # 去重

            try: # 输入prompt_id 和 img_name 获取url
                for img_name in img_name_list:
                    view = requests.get(
                            url=f'{url}/view',
                        params={
                            "filename": img_name,  # 图片名称
                            "type": "output",  # 图片存放位置
                            # "preview": "WEBP"  # 预览格式，可选，添加后下载的图片再上传到服务器会有问题
                        },
                        timeout=10  # 设置请求超时时间
                    )
                    if view.status_code == 200:
                        print(f"图片URL: {view.url}")
                        print(f"生成时间: {(finish_time - start_time) / 1000} 秒")  # 返回生成时间

                        # view.url # 图片url
                        # view.content # 图片二进制流

                        img_url_list.append(view.url) # 将图片url添加到列表

                img_url_list = sorted(img_url_list) # 对文件列表进行升序排序

                result = {
                    # "prompt": prompt,  # 返回prompt
                    "img_url_list": img_url_list,  # 返回图片URL
                    "generate_time": (finish_time - start_time) / 1000  # 返回生成时间
                }
            
                ws.close()  # 关闭连接
                
            except Exception as e:
                print(f"获取生成结果失败: {e}")
                print("Debug: Exception details:", str(e))  # 新增：打印详细的异常信息
                ws.close()  # 关闭连接

    def on_error(ws, error):
        print("错误:", error)
        ws.close()

    def on_close(ws, close_status_code, close_msg):
        print("WebSocket连接已关闭")

    
    # 创建 WebSocket 应用
    ws_app = websocket.WebSocketApp(ws_url,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close)
    
    ws_app.on_open = on_open # 设置连接打开时的回调
    ws_app.run_forever()# 运行 WebSocket 连接

    return result if result else None  # 返回结果或None

# a = generate_image(prompt="1 girl", width=1024, height=1024)
# print(a)