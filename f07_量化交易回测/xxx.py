from dataclasses import dataclass
from datetime import datetime

# 代表一根k线
@dataclass
class Bin:

    # 开始 结束 时间
    open_time: datetime
    close_time: datetime

    # 买入价格
    open_bid: float
    high_bid: float
    low_bid: float
    close_bid: float

    # 卖出价格
    open_ask: float
    high_ask: float
    low_ask: float
    close_ask: float

    # 成交量
    volume: float

    # 辅助变量
    pnl:float
    length:int



# 代表一次交易
@dataclass
class Trade:
    uuid:str # 交易id
    symbol:str # 品种

    in_price:float # 买入价格
    out_price:float # 卖出价格

    stop_loss_price:float # 止损价格
    stop_make_price:float # 止盈价格

    commission_rate:float # 手续费率
    commission:float # 固定手续费

    profit:float # 这笔交易最终盈利

    quantity:int # 交易仓位 交易数量

    in_time:datetime # 买入时间
    out_time:datetime # 卖出时间

    direction:str # 交易方向 做多 做空


# 加载历史数据 单例模式
class data_repository:
    _instance = None  # 类变量，存储唯一实例
    _initialized = False # 确保只初始化一次 不会重复执行
    
    def __new__(cls): # __new__ 方法负责创建实例
        if cls._instance is None: # 只有当实例不存在时才创建
            cls._instance = super().__new__(cls)
        return cls._instance  # 总是返回同一个实例
    
    def __init__(self):
        if not self._initialized: # 初始化代码只执行一次
            self._initialized = True

            self.data_4h = []
            self.data_24h = []
            self.data_1m = []
    
    def load_data(self):
        # 加载数据的逻辑
        pass


class strategy:
    def __init__(self):
        self.k1 = 2.1
        self.k2 = 2.4
        self.k3 = 2.7

    # 实时运行
    def run(self):
        pass

    # 运行回测
    def run_simulation(self):
        # 每隔一段时间 计算一次入场价格
        # 大循环1day
            # 计算一次入场价

            # 小循环1min
                # 如果到达入场价格
                # 创建一个Trade对象

                # 遍历已经创建的Trade对象
                # 检查 止损止盈 是否触发 和 出场条件 并平仓
                # 只有平仓的trade 才会记录到trade_list中
        

# 运行过程中的每一笔交易
trade_list = [] # n个Trade对象


# cost funtion = 夏普比率 胜率 回撤 盈亏pnl曲线 等
# 价格数据 -> 回测 -> 交易记录表 -> 计算各种指标
# 1 夏普
# 2 胜率
# 3 盈亏比
# 4 最大连续亏损次数
# 5 最大回撤
# 6 交易次数
# 7 交易频率
# 8 平均持仓时间
# 9 pnl盈利曲线

# 可视化 cost funtion 结果

''' 
输入一根k线
输出 买入 卖出 信号
'''
def trade_rule(bin: Bin):
    pass
    
# 使用
k = Bin(
    open_time=datetime.now(),
    close_time=datetime.now(),
    open_bid=100,
    high_bid=100,
    low_bid=100,
    close_bid=100,
    open_ask=100,
    high_ask=100,
    low_ask=100,
    close_ask=100,
    volume=100,
    pnl=100,
    length=100,
)
print(k)