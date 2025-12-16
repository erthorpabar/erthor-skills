"""
抽奖系统测试文件
"""
import requests
import time

# 服务器地址
BASE_URL = "http://127.0.0.1:8001"

def print_result(title, response, start_time):
    """打印测试结果"""
    end_time = time.time()
    print(f"\n{'='*60}")
    print(f"📋 {title}")
    print(f"⏱️  耗时: {end_time - start_time:.2f} 秒")
    print(f"📊 状态码: {response.status_code}")
    try:
        print(f"📦 响应数据: {response.json()}")
    except:
        print(f"📦 响应数据: {response.text}")
    print(f"{'='*60}")

def test_health_check():
    """测试1: 健康检查"""
    start = time.time()
    url = f"{BASE_URL}/"
    response = requests.get(url)
    print_result("健康检查", response, start)
    return response

def test_get_stock():
    """测试2: 查询库存"""
    start = time.time()
    url = f"{BASE_URL}/stock"
    response = requests.get(url)
    print_result("查询库存", response, start)
    return response

def test_lottery(user_id, username):
    """测试3: 抽奖"""
    start = time.time()
    url = f"{BASE_URL}/lottery"
    data = {
        "user_id": user_id,
        "username": username
    }
    response = requests.post(url, json=data)
    print_result(f"抽奖 - 用户{username}", response, start)
    return response

def test_get_order(order_id):
    """测试4: 查询订单"""
    start = time.time()
    url = f"{BASE_URL}/order/{order_id}"
    response = requests.get(url)
    print_result(f"查询订单 - {order_id}", response, start)
    return response

def test_pay_order(order_id):
    """测试5: 完成支付"""
    start = time.time()
    url = f"{BASE_URL}/order/{order_id}/pay"
    response = requests.post(url)
    print_result(f"完成支付 - {order_id}", response, start)
    return response

def test_cancel_order(order_id):
    """测试6: 放弃支付"""
    start = time.time()
    url = f"{BASE_URL}/order/{order_id}/cancel"
    response = requests.post(url)
    print_result(f"放弃支付 - {order_id}", response, start)
    return response

def test_get_all_orders():
    """测试7: 查询所有订单"""
    start = time.time()
    url = f"{BASE_URL}/orders"
    response = requests.get(url)
    print_result("查询所有订单", response, start)
    return response

def test_reset_system():
    """测试8: 重置系统"""
    start = time.time()
    url = f"{BASE_URL}/reset"
    response = requests.post(url)
    print_result("重置系统", response, start)
    return response

# ——————————————————————————————————————————————————————————————
# 主测试流程
# ——————————————————————————————————————————————————————————————

if __name__ == "__main__":
    print("\n" + "🎰"*30)
    print("开始测试抽奖系统".center(60))
    print("🎰"*30 + "\n")
    
    try:
        # 1️⃣ 健康检查
        test_health_check()
        
        # 2️⃣ 查询初始库存
        test_get_stock()
        
        # 3️⃣ 测试抽奖（多次抽奖直到中奖）
        order_id = None
        for i in range(10):  # 最多尝试10次
            response = test_lottery(f"user_{i}", f"测试用户{i}")
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    order_id = data.get("order_id")
                    print(f"\n🎉 第{i+1}次抽奖中奖！订单ID: {order_id}")
                    break
                else:
                    print(f"\n😢 第{i+1}次抽奖未中奖")
        
        if order_id:
            # 4️⃣ 查询临时订单
            test_get_order(order_id)
            
            # 5️⃣ 完成支付
            test_pay_order(order_id)
            
            # 6️⃣ 再次查询订单（应该显示已支付）
            test_get_order(order_id)
        
        # 7️⃣ 再次抽奖测试取消支付
        cancel_order_id = None
        for i in range(10, 20):  # 再抽10次
            response = test_lottery(f"user_{i}", f"测试用户{i}")
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    cancel_order_id = data.get("order_id")
                    print(f"\n🎉 第{i+1}次抽奖中奖！订单ID: {cancel_order_id}")
                    break
        
        if cancel_order_id:
            # 8️⃣ 测试放弃支付
            test_cancel_order(cancel_order_id)
            
            # 9️⃣ 查询取消后的订单（应该不存在）
            test_get_order(cancel_order_id)
        
        # 🔟 查询所有已支付订单
        test_get_all_orders()
        
        # 1️⃣1️⃣ 查看最终库存
        test_get_stock()
        
        # 1️⃣2️⃣ 重置系统（可选，如果需要清空数据）
        # test_reset_system()
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 连接失败！请确保服务器已启动在 http://127.0.0.1:8001")
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
    
    print("\n" + "✅"*30)
    print("测试完成".center(60))
    print("✅"*30 + "\n")