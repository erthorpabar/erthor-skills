''' 
第 1-6 轮: 完整保留所有消息
    ↓
第 7 轮: 触发摘要
    ├─ 生成摘要: "用户叫 Lance,喜欢 49ers..."
    ├─ 删除旧消息: 只保留最后 2 条
    └─ 状态更新: summary + 最新 2 条消息
    ↓
第 8 轮: LLM 看到的上下文
    ├─ SystemMessage("摘要: 用户叫 Lance...")
    └─ 最新的 2 条消息

'''
from langchain_core.messages import RemoveMessage

def summarize_conversation(state: State):
    # 1. 获取现有摘要
    summary = state.get("summary", "")

    # 2. 创建摘要提示
    if summary:
        # 增量摘要: 扩展现有摘要
        prompt = f"Current summary: {summary}\n\nExtend with new messages:"
    else:
        # 首次摘要: 创建新摘要
        prompt = "Create a summary of the conversation:"

    # 3. 调用 LLM 生成摘要
    messages = state["messages"] + [HumanMessage(prompt)]
    response = model.invoke(messages)

    # 4. 删除旧消息,只保留最后 2 条
    delete = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]

    return {
        "summary": response.content,
        "messages": delete
    }


# 第 1 次摘要 (7 条消息)
summary_1 = "Lance 介绍自己,喜欢 49ers..."

# 第 2 次摘要 (又积累了 5 条新消息)
# 提示词: "Current summary: {summary_1}\n\nExtend with new messages..."
summary_2 = "Lance 介绍自己,喜欢 49ers 和 Nick Bosa,询问了防守球员薪资..."



# 实践 1：定期清理消息
def should_cleanup(state: MessagesState) -> bool:
    """每 10 条消息清理一次"""
    return len(state["messages"]) % 10 == 0

builder.add_conditional_edges(
    "chat",
    should_cleanup,
    {True: "cleanup", False: END}
)


# 实践 2：保留系统消息
from langchain_core.messages import SystemMessage

def cleanup_node(state):
    messages = state["messages"]
    # 保留系统消息和最新 5 条对话
    system_messages = [m for m in messages if isinstance(m, SystemMessage)]
    recent_messages = [m for m in messages if not isinstance(m, SystemMessage)][-5:]

    # 删除其他消息
    to_delete = [m for m in messages if m not in system_messages + recent_messages]
    delete_ops = [RemoveMessage(id=m.id) for m in to_delete]

    return {"messages": delete_ops}


# 实践 3：实现消息编辑
def edit_message_node(state):
    """允许用户编辑最后一条消息"""
    last_message = state["messages"][-1]

    # 创建新消息，使用相同的 ID
    edited_message = HumanMessage(
        content=state["edited_content"],
        id=last_message.id,  # ⭐ 相同 ID = 覆盖
        name=last_message.name
    )

    return {"messages": [edited_message]}