import requests
import os
import json
import time 

from core.config import settings



def upload_img(img_path: str):
    url = settings.COMFYUI_API_URL
    # url = "http://61.49.53.9:6017" # 测试打开

    # 如果图片路径是http，则下载图片
    if img_path.startswith("http"):
        img_name = f"{int(time.time())}.png"
        with open(img_name, 'wb') as f:
            f.write(requests.get(img_path).content)
        img_path = img_name # 更新图片路径

    # 如果是路径，则上传图片
    with open(img_path, 'rb') as f:
        response = requests.post(
            url=f'{url}/upload/image',
            files={'image': f},
        )
        
    # 修改为始终删除本地文件
    if os.path.exists(img_path):  # 检查文件是否存在
        os.remove(img_path)  # 删除本地文件
    
    return response
    


# response = upload_img("ccc.png")
# print(response.json())
