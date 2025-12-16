

import os
import time
from pprint import pprint

# ——————————加载环境变量——————————
from dotenv import load_dotenv
load_dotenv()

# ——————————异步库(可多线程 可多协程)——————————
import asyncio

# ——————————http请求库——————————
import requests

# ——————————线程管理工具——————————
from concurrent.futures import ThreadPoolExecutor

# ——————————读取环境变量——————————
api_url = os.getenv("LLM_URL")
api_key = os.getenv("LLM_API_KEY")
model = os.getenv("LLM_MODEL")


# ——————————————————————同步请求函数————————————————————
# 全局session 请求前只建立一次连接
session = requests.Session()

def chat(messages):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "model": model,
        "messages": messages
    }

    response = session.post(api_url, headers=headers, json=data)
    answer = response.json()["choices"][0]["message"]["content"]
    
    return answer

# ——————————————————————多线程并行————————————————————
# 1 收集所有待请求任务
n = 3 # 并发量
messaages_list = [
    [
        {"role": "system", "content": "你是一个猫娘，如果对方提问，需要在结束时加上主人喵"},
        {"role": "user", "content": "今天中文我应该吃什么？"}
    ]
] * n  # 注意这里的乘法应该在外面


# 2 运行
start_time = time.time()

async def main():
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=n) as executor: # 创建线程池 包含n个线程
        tasks = [loop.run_in_executor(executor, chat, m) for m in messaages_list]
        answers = await asyncio.gather(*tasks) # 等待所有线程完成一起返回
    return answers
answers = asyncio.run(main())

end_time = time.time()


# 3 打印
print(f"多线程并行耗时: {end_time - start_time} 秒")
print('并发量:', len(answers))
pprint(answers)



