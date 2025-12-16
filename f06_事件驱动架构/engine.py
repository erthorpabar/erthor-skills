from threading import Thread # 多线程
from queue import Empty, Queue # 队列


from typing import Any, Callable
from collections import defaultdict # 字典 如果key不存在 则自动创建
from time import sleep

''' 
1 队列中有多种 tpye 事件类型
2 一个event 的 data 可以被多个 模块取走

event1 = Event(type=1, data=1)
event2 = Event(type=2, data=2)
↓
put(event) 放入队列
'''


EVENT_TIMER = "eTimer"
EVENT_CTA_STRATEGY = "eCtaStrategy"

# 事件结构体
class Event:
    def __init__(self, type:str, data: Any = None):
        self.type = type
        self.data = data

# Callable[[参数类型], 返回类型]
HandlerType = Callable[[Event], None] # None 表示无返回值

# 事件引擎
class EventEngine:
    def __init__(self, interval:int=1):
        self._interval = interval
        self._queue = Queue() # 队列
        self._active = False # 运行状态

        # target 指定 线程启动 要 执行的函数
        self._thread = Thread(target=self._run)
        self._timer = Thread(target=self._run_timer)

        # 特定类型事件
        self._handlers = defaultdict(list) # 访问不存在的key 自动创建空列表[]作为value
        # 通用事件
        self._general_handlers = []

    
    # ——————基础函数——————

    ''' 
    输入
    event = Event(
        type="eCtaStrategy", 
        data={"strategy_name": "double_ma", "action": "buy"}
    )

    handlers = {
        "eCtaStrategy": [func1, func2, func3]
    }

    计算过程
    event.type = "eCtaStrategy"
    handler = func1 (第一次循环)
    
    执行
    func1(event)
    '''
    def _process(self, event:Event):
        if event.type in self._handlers:
            for handler in self._handlers[event.type]:
                if event.type == EVENT_CTA_STRATEGY:
                    print("hander", handler)
                    print(event.type, event.__dict__)
                handler(event)
        
        if self._general_handlers:
            for handler in self._general_handlers:
                handler(event)
    
        
    def _run(self):
        while self._active: # 当处于运行状态
            try:
                # 1 获取事件
                event = self._queue.get(block=True, timeout=1) # 不断从队列中获取事件 阻塞等待
                # 2 处理事件
                # 如果有函数处理 则执行
                # 如果没有函数处理 则跳过
                self._process(event) # 处理事件
            except Empty: 
                pass
    
    # 每1s 将一个type=EVENT_TIMER 的事件 放入队列
    def _run_timer(self):
        while self._active: # 当处于运行状态
            sleep(self._interval)
            event = Event(type=EVENT_TIMER)
            self._queue.put(event)
    
    def start(self):
        self._active = True  
        self._thread.start() 
        self._timer.start()  
    

    def stop(self):
        self._active = False  
        self._timer.join()  
        self._thread.join() 

    # 事件 -> 队列
    def put(self, event:Event):
        self._queue.put(event)

    
    # 将函数注册为订阅者
    def register(self, type:str, func:Callable):
        self._subscribers[type].add(func)
    
    # 将函数取消注册为订阅者
    def unregister(self, type:str, func:Callable):
        self._subscribers[type].remove(func)
    

if __name__ == '__main__':
    engine = EventEngine()
    engine.start()
    engine.register('tick', lambda event: print(event))
    engine.register('etimer', lambda event: print(event))
    engine.stop()