''' 
py 
GIL 全局解释器锁 
多线程 只能 使用一个cpu核心的算力

如果需要充分利用多核cpu的算力 就需要多进程
'''

from multiprocessing import Process

if __name__ == "__main__":
    ''' 
    p = Process() 不能写在全局区域(否则会递归)
    '''
    p_list = []
    for i in range(10):
        p = Process(target=print, args=("hello",)) # 创建进程
        p.start() # 启动进程
        p_list.append(p) # 添加进程到列表
    for p in p_list:
        p.join() # 等待进程结束

