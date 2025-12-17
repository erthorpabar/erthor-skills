
'''
collection 集合 = 一个表
field 字段 = 列名称
index 索引 = 索引名称
entity 实体 = 一条数据 = (index ,field1,field2)
'''

from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
import numpy as np
# ========== 配置 ==========
MILVUS_HOST = "localhost"
MILVUS_PORT = 19530
COLLECTION_NAME = "demo_collection"
DIM = 128  # 向量维度


# ========== 1. 连接 Milvus ==========
print("\n【1】连接 Milvus...")

connections.connect(
        alias="default",
        host=MILVUS_HOST,
        port=MILVUS_PORT
    )

print("✅ 已连接到 Milvus")


# ========== 2. 创建集合 ==========
print("\n【2】创建集合...")

# 如果集合已存在，先删除
if utility.has_collection(COLLECTION_NAME):
    utility.drop_collection(COLLECTION_NAME)
    print(f"🗑️  删除旧集合: {COLLECTION_NAME}")

# 定义字段
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=500),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=DIM)
]

# 创建集合
schema = CollectionSchema(fields=fields, description="简单的向量集合")
collection = Collection(name=COLLECTION_NAME, schema=schema)

# 创建索引（加速搜索）
index_params = {
    "index_type": "IVF_FLAT",
    "metric_type": "L2",
    "params": {"nlist": 128}
}
collection.create_index(field_name="embedding", index_params=index_params)

print(f"✅ 创建集合: {COLLECTION_NAME}")
print(f"   字段: id, text, embedding({DIM}维)")

# ========== 3. 插入数据 ==========
print("\n【3】插入数据...")

# 生成随机向量数据
num_entities = 100
texts = [f"文本_{i}" for i in range(num_entities)]
embeddings = np.random.random((num_entities, DIM)).tolist()

# 插入数据
entities = [texts, embeddings]
insert_result = collection.insert(entities)

# 加载集合到内存（必须）
collection.load()

print(f"✅ 插入了 {num_entities} 条数据")
print(f"   插入的ID数量: {len(insert_result.primary_keys)}")

# ========== 4. 统计信息 ==========
print("\n【4】集合统计...")
print(f"📊 集合名称: {collection.name}")
print(f"📊 数据数量: {collection.num_entities}")
print(f"📊 字段列表:")
for field in collection.schema.fields:
    print(f"   - {field.name}: {field.dtype}")


# ========== 5. 查询数据 ==========
print("\n【5】查询数据（前5条）...")

results = collection.query(
    expr="id >= 0",
    output_fields=["id", "text"],
    limit=5
)

print("📋 查询结果:")
for entity in results:
    print(f"   id={entity['id']}, text={entity['text']}")


# ========== 6. 搜索向量 ==========
print("\n【6】搜索最相似的向量...")

# 生成查询向量
search_vectors = np.random.random((1, DIM)).tolist()

# 搜索参数
search_params = {
    "metric_type": "L2",
    "params": {"nprobe": 10}
}

# 执行搜索（返回前5个最相似的结果）
results = collection.search(
    data=search_vectors,
    anns_field="embedding",
    param=search_params,
    limit=5,
    output_fields=["text"]
)

print("🔍 搜索结果（Top 5）:")
for i, hits in enumerate(results):
    print(f"   查询向量 {i}:")
    for j, hit in enumerate(hits):
        print(f"      {j+1}. id={hit.id}, 距离={hit.distance:.4f}, 文本={hit.entity.get('text')}")


# ========== 7. 更多查询示例 ==========
print("\n【7】条件查询...")

# 查询特定范围的数据
results = collection.query(
    expr="id in [449000000000000000, 449000000000000001, 449000000000000002]",
    output_fields=["id", "text"]
)

if results:
    print(f"📋 找到 {len(results)} 条匹配数据:")
    for entity in results[:3]:  # 只显示前3条
        print(f"   id={entity['id']}, text={entity['text']}")
else:
    print("📋 未找到匹配数据（ID可能不存在）")

# 查询文本包含特定内容（使用 like）
results = collection.query(
    expr='text like "文本_1%"',
    output_fields=["id", "text"],
    limit=5
)

print(f"\n📋 文本匹配查询（文本_1开头）:")
for entity in results:
    print(f"   id={entity['id']}, text={entity['text']}")



# ========== 8. 完成 ==========
print("\n【8】清理...")

# 释放集合（可选）
# collection.release()
# print("✅ 已释放集合")

# 删除集合（可选，取消注释以启用）
# utility.drop_collection(COLLECTION_NAME)
# print(f"🗑️  已删除集合: {COLLECTION_NAME}")

# 断开连接
connections.disconnect("default")
print("👋 断开连接")

print("\n" + "=" * 50)
print("✅ 所有操作完成!")
print("=" * 50)