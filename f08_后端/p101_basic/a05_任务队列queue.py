''' 任务队列
写入大量任务 -> 任务队列queue -> 并行处理

'''
from queue import Queue,Empty
import threading
import time
from concurrent.futures import ThreadPoolExecutor

# 1 初始化队列
q = Queue()

# 2 写入大量任务
q.put({"prompt":"1 girl"})
q.put({"prompt":"1 cat"})
q.put({"prompt":"1 boy"})
q.put({"prompt":"1 apple"})

# 3 定义作图函数
def generate_image():
    while True:
        try:
            task = q.get(timeout=1) # 当空队列时 会触发超过1s 拿不到任务 然后退出
            print(f'线程{threading.get_ident()} 获取到任务 {task}')
            time.sleep(5) # 任务耗时
            print(f'线程{threading.get_ident()} 完成任务 {task}')
            q.task_done()  # 标记任务完成
        except Empty:
            break # 队列空了 退出

# 4 多线程 并行处理
workers = 2
with ThreadPoolExecutor(max_workers=workers) as pool: 
    for i in range(workers):
        pool.submit(generate_image)

# 5 等待所有任务完成
print("所有任务已完成，线程池已关闭。")