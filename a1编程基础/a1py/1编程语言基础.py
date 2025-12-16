

# 1 变量赋值
a = 1 
b = 2

# 2 打印输出
print(a) # 值
print(type(a)) # 类型
print(len(a)) # 长度

# 3 数据类型 和 数据结构
aint = 1
afloat = 1.0
astr = "hello"
alist = [4,5,6]
adict = {"a":1,"b":2}

# 4 运算规则
print(a + b)

# 5 条件判断
if a > b:
    print("a > b")
else:
    print("a <= b")

# 6 循环
for i in alist:
    print(i)

# 7 定义函数 与 变量的作用域
def add(a,b):
    print(a + b) # 打印值
    return a + b # 返回值
a = add(1,2)
# 作用域：函数不能访问外部变量

# 8 定义类
class Person:
    def __init__(self,name,age): # 初始化直接运行
        self.name = name
        self.age = age
        print(f"{self.name}出生了")

    def say_hello(self):
        print(f"hello, my name is {self.name} and I am {self.age} years old")

tom = Person("tom",18) # 初始化，并定义初始属性
tom.say_hello()

# 9 调包
import random
print(random.randint(1,10))


























