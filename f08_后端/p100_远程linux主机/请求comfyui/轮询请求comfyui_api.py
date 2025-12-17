# ——————————————导入包————————————————
import requests
import json
import random
import time

from PIL import Image
from io import BytesIO


# ——————定义函数——————
def generate_image(url, prompt, width, height):
    print("————————————————start————————————————————")

    # ——————————打开工作流——————————
    with open('flux_api.json', 'r', encoding='utf-8') as file:
        work_flow = json.load(file)

    # ——————————修改参数————————————
    work_flow['116']['inputs']['text'] = prompt # 提示词
    work_flow['104']['inputs']['width'] = width # 宽
    work_flow['104']['inputs']['height'] = height # 高
    work_flow['102']['inputs']['seed'] = random.randint(0, 4294967295)
    '''
    备注：
    连续输入两次同样的值，comfyui不会重复执行。这是comfyui的机制。
    所以要设置随机种子确保每次输入不会重复。
    '''

    # ————————请求1执行生图任务，获取prompt_id——————————
    process = requests.post(
            url=f'{url}/prompt',
            json={"prompt": work_flow},
        )
    print('是否提交任务:', True if process.status_code == 200 else False)

    prompt_id = process.json()['prompt_id']
    print('任务prompt_id:', prompt_id)

    # ——————请求2根据prompt_id，获取图片名称——————————
    # <<<等待生图完成，才能够获取图片名称>>>
    # 可用轮询等待
    start_time = time.time()   # 记录开始时间
    time.sleep(2) # 正常生图时间估算
    retry = 0

    while retry < 6: # 重复查询最多n次
        time.sleep(1) 
        history = requests.get(
            url=f'{url}/history',
            json={"prompt_id": prompt_id},
        )

        if history.status_code == 200:
            try:
                history_json = history.json()
                if prompt_id in history_json:
                    img_name = history_json[prompt_id]['outputs']['106']['images'][0]['filename']
                    print('图片名称:', img_name)
                    break
            except:
                print(retry)
            retry = retry + 1
    end_time = time.time()  # 记录结束时间
    generate_time = end_time - start_time
    print('生图+返图时间:', generate_time)
    print('超时retry次数:', retry)
    print('是否获取图片名称:', True if history.status_code == 200 else False)


    # ————请求3根据prompt_id和图片名称，获取图片内容——————
    if 'img_name' in locals():
        view = requests.get(
            url=f'{url}/view',
                params={
                "filename": img_name,  # 图片名称
                "type": "output",  # 图片存放位置
                # "subfolder": "subfolderName",  # 如果有子文件夹，取消注释并设置子文件夹名称
                # "channel": "rgb"  # 可选，设置颜色通道
            }
        )
        print('是否获取二进制图片内容:', True if view.status_code == 200 else False)

        if view.status_code == 200:
            # 手动创建outputs文件夹

            # 保存到本地
            image = Image.open(BytesIO(view.content)) # 二进制保存
            image.save(f"outputs/{img_name}") 

            # 保存对应prompt
            with open(f"outputs/{img_name[:-3]}"+"txt", "w") as file:
                file.write(prompt)

            # return view.content # 返回二进制文件
            # return view.url # 返回网址链接
        else:
            return None
    else:
        print('未能获取图片名称，无法继续处理。')
        return None
    
    print("————————————————end——————————————————————")

# ——————调用函数——————

url = "http://106.13.33.123:6002" 
prompt = '''
1 girl,
'''
width = 1024
height = 1024

image = generate_image(url, prompt, width, height)



# ———————————————————————调用思路————————————————————————————
'''
- /object_info接口，全局一次性获取各种可用的配置信息
- /ws接口，建立连接，返回实时监听信息，包括队列任务数量等
1 /prompt接口，发送任务
<<<等待任务完成>>>
2 /history接口，拿到任务id从而获取文件名
3 /view接口，文件链接地址，可预览或下载


api文件写在comfyui中的server.py中
'''

# ——————————————————————接口文档地址————————————————————————
# comfyui文档 https://www.yunrobot.cn/showdoc/web/#/641840309
# webui文档 https://www.yunrobot.cn/showdoc/web/#/641840286



# ————————————图生图———————————————
# 把素材上传到comfyui/input中，comfyui会自动调用

# # 图片地址
# path = 'x.png'

# # 上传图片
# up_img = requests.post(
#     url=f'{url}/upload/image',
#     files={'image': open(path, 'rb')},
# )

# # 查看任务状态
# print(up_img)



# ——————————————————————————各种其他请求—————————————————————————————————————
# # 获取所有可用参数
# info=requests.get(url=f'{url}/object_info')
# print(info.json())

# # 查看所有ckpt
# checkpoints=requests.get(url=f'{url}/object_info/CheckpointLoaderSimple')
# print(checkpoints.json()['CheckpointLoaderSimple']['input']['required']['ckpt_name'][0])

# # 查看所有vae
# vae=requests.get(url=f'{url}/object_info/VAELoader')
# print(vae.json()['VAELoader']['input']['required']['vae_name'][0])

# # 查看当前任务数量
# process_number=requests.get(url=f'{url}/prompt') # 获取任务数量
# print(process_number.json()['exec_info']['queue_remaining'])



# ——————————————————————其他部署项目————————————————————
# comfyui部署
# https://github.com/BennyKok/comfyui-deploy
# https://github.com/piyushK52/comfy-runner































