

import os
import time
from pprint import pprint

# ——————————加载环境变量——————————
from dotenv import load_dotenv
load_dotenv()

# ——————————异步库(可多线程 可多协程)——————————
import asyncio

# ——————————多协程http请求库——————————
import aiohttp




# ——————————读取环境变量——————————
api_url = os.getenv("LLM_URL")
api_key = os.getenv("LLM_API_KEY")
model = os.getenv("LLM_MODEL")


# ——————————————————————异步请求函数————————————————————
async def as_chat(session,messages):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "model": model,
        "messages": messages
    }

    # requests库无多协程版本 可以用多线程来实现异步 asyncio.to_thread(函数(参数))
    # aiphttp库有多协程版本 这个写法开销更小
    async with session.post(api_url, headers=headers, json=data) as response:
        answer = (await response.json())["choices"][0]["message"]["content"] 
    
    return answer

# ————————————————————多协程 并发——————————————————————
# 1 收集所有待请求数据
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
    async with aiohttp.ClientSession() as session: # 全局session 请求前只建立一次连接
        tasks = [as_chat(session, messages) for messages in messaages_list]
        answers = await asyncio.gather(*tasks)
        return answers
answers =  asyncio.run(main())

end_time = time.time()


# 3 打印
print(f"异步并发耗时: {end_time - start_time} 秒")
print('并发量:',len(answers))
pprint(answers)



