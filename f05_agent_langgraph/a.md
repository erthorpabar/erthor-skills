





# 4 
# breakpoint 人机协助
三种方法
====================
1. interrupt_before (执行前中断)
# 在执行 tools 节点前暂停,等待人工批准
app = graph.compile(
    checkpointer=memory,
    interrupt_before=["tools"]  # 在工具调用前暂停
)

# 执行
config = {"configurable": {"thread_id": "1"}}
result = app.invoke(input, config)  # 暂停在工具调用前

# 人工审查后继续
result = app.invoke(None, config)  # 继续执行
====================
2. interrupt_after (执行后中断)
# 在执行 tools 节点后暂停,查看结果
app = graph.compile(
    checkpointer=memory,
    interrupt_after=["tools"]  # 工具调用后暂停
)

====================
3. 动态中断 (NodeInterrupt)
from langgraph.types import interrupt

def approval_node(state):
    # 根据条件决定是否需要人工审批
    if state["amount"] > 10000:
        decision = interrupt({
            "message": f"需要批准: ${state['amount']} 的支付",
            "data": state["payment_details"]
        })
        if decision != "approved":
            return {"status": "rejected"}
    return {"status": "approved"}

======================
场景 1: 金融交易审批 💰
     
def payment_agent():
    # 构建图
    graph = StateGraph(PaymentState)
    graph.add_node("analyze", analyze_transaction)
    graph.add_node("execute", execute_payment)

    # 高风险交易需要人工审批
    def risk_router(state):
        if state["risk_score"] > 0.7:
            return "approval"  # 跳转到审批节点
        return "execute"  # 直接执行

    graph.add_conditional_edges("analyze", risk_router)

    # 在审批节点前中断
    app = graph.compile(interrupt_before=["approval"])
======================
场景 2: 内容审核 📝
# 生成内容后,发布前需要人工审查
app = graph.compile(
    interrupt_after=["content_generation"],
    interrupt_before=["publish"]
)

# 工作流
# 1. 生成内容 (自动)
# 2. 暂停 → 人工审查
# 3. 批准后 → 发布
======================
场景 3: 医疗诊断 🏥

class DiagnosisState(TypedDict):
    symptoms: list
    diagnosis: str
    confidence: float

def diagnosis_node(state):
    diagnosis, confidence = ai_diagnose(state["symptoms"])

    # 低置信度需要医生确认
    if confidence < 0.9:
        doctor_input = interrupt({
            "ai_diagnosis": diagnosis,
            "confidence": confidence,
            "request": "请医生确认或修正诊断"
        })
        diagnosis = doctor_input["final_diagnosis"]

    return {"diagnosis": diagnosis}

====================
场景 4: 代码部署 🚀
# CI/CD 流程
graph.add_node("test", run_tests)
graph.add_node("deploy", deploy_to_production)

# 部署到生产前需要手动批准
app = graph.compile(interrupt_before=["deploy"])

# 工作流:
# 1. 运行测试 (自动)
# 2. 测试通过 → 暂停
# 3. DevOps 审查 → 批准
# 4. 部署到生产 (自动)
======================
# 完整示例
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
app = graph.compile(
    checkpointer=memory,  # 必需: 保存状态
    interrupt_before=["critical_node"]
)

config = {"configurable": {"thread_id": "user123"}}

# 第一次调用: 执行到断点
result = app.invoke(input, config)

# 检查状态
state = app.get_state(config)
print(state.values)  # 当前状态
print(state.next)    # 下一个要执行的节点

# 人工决策后继续
result = app.invoke(None, config)  # None 表示继续执行
======================
# 编译时设置断点
app = graph.compile(
    checkpointer=memory,
    interrupt_before=["human_review"]  # 在这个节点前暂停
)

# 执行
app.invoke(input, config)

# 此时程序暂停,可以:
state = app.get_state(config)
print(state.values)  # 查看当前状态

# 修改状态
app.update_state(config, {"approved": True})

# 继续执行
app.invoke(None, config)



# 5
# 流式
# invoke: 等全部完成
result = app.invoke(input, config)

# stream: 逐步返回
for chunk in app.stream(input, config):
    print(chunk)  # 每个节点完成后输出

# astream_events: token 级流式
async for event in app.astream_events(input, config):
    if event["event"] == "on_chat_model_stream":
        print(event["data"]["chunk"].content, end="")



# 6 
# store 保存用户信息
https://www.learngraph.online/learngraph/module-1%20%E5%9F%BA%E7%A1%80%E6%A6%82%E5%BF%B5/1.6-%E6%9C%AF%E8%AF%AD%E6%B1%87%E6%80%BB%E4%B8%8E%E8%AF%A6%E7%BB%86%E4%BB%8B%E7%BB%8D.html#%F0%9F%94%B5-16-saver-vs-store-%E5%AF%B9%E6%AF%94%E4%B8%8E%E8%81%94%E7%B3%BB
# 业务数据(用户偏好、知识库等) 用户画像、知识库、历史记录

场景 1: 客服聊天机器人
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.store.memory import InMemoryStore

# 1️⃣ Saver: 保存 workflow 状态
checkpointer = SqliteSaver.from_conn_string("checkpoints.db")
app = graph.compile(checkpointer=checkpointer)

# 每次调用自动保存状态
config = {"configurable": {"thread_id": "user_123"}}
app.invoke({"messages": [("user", "你好")]}, config)
app.invoke({"messages": [("user", "再见")]}, config)  # 记住上次对话

# 查看历史状态(Time Travel)
for state in app.get_state_history(config):
    print(state.values)

# 2️⃣ Store: 保存 agent 的长期记忆
store = InMemoryStore()

# 手动存储用户信息
store.put(
    namespace=("users", "user_123"),
    key="profile",
    value={
        "name": "Alice",
        "preferences": {"language": "zh", "theme": "dark"},
        "last_login": "2025-01-13"
    }
)

# 手动读取
profile = store.get(namespace=("users", "user_123"), key="profile")
print(f"用户名: {profile.value['name']}")

# 搜索记忆
active_users = store.search(
    namespace=("users",),
    filter={"last_login": {"$gte": "2025-01-01"}}
)

# Saver: 记录对话状态
# - 用户说了什么
# - AI 回复了什么
# - 当前在哪个节点
# - 调用了哪些工具

# Store: 记录用户信息
# - 用户姓名、联系方式
# - 历史订单
# - 偏好设置
# - 常见问题

场景 2: 个人助理 Agent
# Saver: 保存当前任务状态
app = graph.compile(checkpointer=PostgresSaver(...))

# 用户: "帮我规划一个日本旅行"
# Saver 自动保存:
# - 当前正在规划日本旅行
# - 已经查询了机票价格
# - 下一步要查酒店

# Store: 保存长期偏好
store.put(
    namespace=("users", "alice"),
    key="travel_preferences",
    value={
        "budget": "中等",
        "喜欢的城市": ["东京", "京都"],
        "避免": ["极限运动"]
    }
)

# 下次对话时,Agent 可以读取这些偏好
prefs = store.get(namespace=("users", "alice"), key="travel_preferences")
# "记得您喜欢东京和京都,我优先推荐这些地方"



场景3 两者都用
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore

# 1. 创建两个持久化系统
checkpointer = PostgresSaver(...)  # 保存 workflow 状态
store = PostgresStore(...)           # 保存长期记忆

# 2. 编译时传入
app = graph.compile(
    checkpointer=checkpointer,  # 自动管理状态
    store=store                  # Agent 可以主动读写
)

# 3. 在节点中使用 Store
def personalized_agent(state, *, store):
    # 读取用户偏好(从 Store)
    user_id = state["user_id"]
    preferences = store.get(("users", user_id), "preferences")

    # 基于偏好生成回复
    response = llm.invoke([
        SystemMessage(f"用户偏好: {preferences.value}"),
        *state["messages"]
    ])

    return {"messages": [response]}
