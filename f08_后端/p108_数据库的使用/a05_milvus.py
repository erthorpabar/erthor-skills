
''' 
milvus 没有命令行交互

'''

# ——————————当前文件夹路径加入搜索路径——————————
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ——————————加载环境变量——————————
from dotenv import load_dotenv
load_dotenv()

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 🔵 Milvus配置
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_USER: str = ""  # 开源版本默认无需用户名
    MILVUS_PASSWORD: str = ""  # 开源版本默认无需密码
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"
        case_sensitive = True

settings = Settings()


# ——————————Milvus 客户端（单例）——————————
from threading import Lock
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
import numpy as np
from typing import List, Dict, Any, Optional

class SingletonMeta(type):
    _instances = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]

class MilvusClient(metaclass=SingletonMeta):
    def __init__(self, host: str, port: int, user: str = "", password: str = ""):
        self.host = host
        self.port = port
        self.alias = "default"
        
        # 连接 Milvus
        connections.connect(
            alias=self.alias,
            host=host,
            port=port,
            user=user,
            password=password
        )
        print(f'✅ Milvus连接成功 ({host}:{port})')

    def ping(self):
        """测试连接"""
        try:
            collections = utility.list_collections()
            print(f'✅ Milvus 连接正常，当前集合数: {len(collections)}')
            return True
        except Exception as e:
            print(f'❌ Milvus 连接失败: {e}')
            return False

    def create_collection(self, name: str, dim: int = 384, description: str = ""):
        """
        创建集合
        
        Args:
            name: 集合名称
            dim: 向量维度
            description: 描述
        """
        # 检查集合是否已存在
        if utility.has_collection(name):
            print(f'⚠️ 集合 {name} 已存在')
            return Collection(name)
        
        # 定义字段
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=1000),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim)
        ]
        
        # 创建集合
        schema = CollectionSchema(fields=fields, description=description)
        collection = Collection(name=name, schema=schema)
        
        # 创建索引
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        collection.create_index(field_name="embedding", index_params=index_params)
        
        print(f'✅ 集合 {name} 创建成功（维度: {dim}）')
        return collection

    def insert(self, collection_name: str, texts: List[str], embeddings: List[List[float]]):
        """
        插入数据
        
        Args:
            collection_name: 集合名称
            texts: 文本列表
            embeddings: 向量列表
        """
        if not utility.has_collection(collection_name):
            raise ValueError(f"集合 {collection_name} 不存在")
        
        collection = Collection(collection_name)
        
        # 插入数据
        data = [texts, embeddings]
        insert_result = collection.insert(data)
        collection.flush()
        
        print(f'✅ 插入 {len(texts)} 条数据到 {collection_name}')
        return insert_result.primary_keys

    def search(
        self, 
        collection_name: str, 
        query_vectors: List[List[float]], 
        top_k: int = 5
    ) -> List[List[Dict[str, Any]]]:
        """
        向量搜索
        
        Args:
            collection_name: 集合名称
            query_vectors: 查询向量列表
            top_k: 返回最相似的前 k 个结果
            
        Returns:
            搜索结果列表
        """
        if not utility.has_collection(collection_name):
            raise ValueError(f"集合 {collection_name} 不存在")
        
        collection = Collection(collection_name)
        
        # 加载集合到内存
        if not collection.is_loaded:
            collection.load()
        
        # 搜索参数
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10}
        }
        
        # 执行搜索
        results = collection.search(
            data=query_vectors,
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["text"]
        )
        
        # 格式化结果
        formatted_results = []
        for hits in results:
            hit_list = []
            for hit in hits:
                hit_list.append({
                    "id": hit.id,
                    "distance": hit.distance,
                    "text": hit.entity.get("text")
                })
            formatted_results.append(hit_list)
        
        return formatted_results

    def delete_collection(self, name: str):
        """删除集合"""
        if utility.has_collection(name):
            utility.drop_collection(name)
            print(f'✅ 集合 {name} 已删除')
        else:
            print(f'⚠️ 集合 {name} 不存在')

    def list_collections(self) -> List[str]:
        """列出所有集合"""
        return utility.list_collections()

    def close(self):
        """断开连接"""
        connections.disconnect(self.alias)
        print('✅ Milvus连接已关闭')


# ——————————测试——————————
async def test_milvus():
    # 创建客户端
    client = MilvusClient(
        host=settings.MILVUS_HOST,
        port=settings.MILVUS_PORT
    )
    
    # 测试连接
    client.ping()
    
    # 创建集合
    collection_name = "test_collection"
    client.create_collection(collection_name, dim=384)
    
    # 插入测试数据
    texts = [
        "人工智能是未来的方向",
        "机器学习改变世界",
        "深度学习很强大"
    ]
    embeddings = [np.random.rand(384).tolist() for _ in range(3)]
    
    ids = client.insert(collection_name, texts, embeddings)
    print(f"插入的IDs: {ids}")
    
    # 搜索
    query_vector = [np.random.rand(384).tolist()]
    results = client.search(collection_name, query_vector, top_k=2)
    
    print("\n搜索结果:")
    for i, hits in enumerate(results):
        print(f"查询 {i+1}:")
        for hit in hits:
            print(f"  - ID: {hit['id']}, 距离: {hit['distance']:.4f}, 文本: {hit['text']}")
    
    # 列出所有集合
    print(f"\n所有集合: {client.list_collections()}")
    
    # 清理：删除测试集合
    client.delete_collection(collection_name)
    
    # 关闭连接
    client.close()


# ——————————实际应用示例：RAG（检索增强生成）——————————
class RAGSystem:
    """结合向量数据库的 RAG 系统示例"""
    
    def __init__(self, milvus_client: MilvusClient, collection_name: str = "knowledge_base"):
        self.client = milvus_client
        self.collection_name = collection_name
        
        # 创建知识库集合
        self.client.create_collection(collection_name, dim=384, description="知识库")
    
    def add_documents(self, texts: List[str]):
        """添加文档到知识库"""
        # 这里应该使用真实的 embedding 模型
        # 例如: from sentence_transformers import SentenceTransformer
        # model = SentenceTransformer('all-MiniLM-L6-v2')
        # embeddings = model.encode(texts)
        
        # 示例：使用随机向量
        embeddings = [np.random.rand(384).tolist() for _ in texts]
        
        return self.client.insert(self.collection_name, texts, embeddings)
    
    def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        """检索相关文档"""
        # 将查询转换为向量
        query_vector = [np.random.rand(384).tolist()]  # 应使用真实 embedding
        
        results = self.client.search(self.collection_name, query_vector, top_k)
        return results[0] if results else []


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_milvus())


'''
实际使用建议：

1. 🎯 向量化模型选择
   - 文本: sentence-transformers (如 all-MiniLM-L6-v2)
   - 图片: CLIP, ResNet
   - 多模态: CLIP
   
2. 📊 索引类型选择
   - FLAT: 精确搜索，适合小数据集
   - IVF_FLAT: 适中性能和精度
   - IVF_SQ8: 压缩存储，适合大数据集
   - HNSW: 高性能，内存占用大
   
3. 🔍 距离度量
   - L2: 欧几里得距离（常用于文本向量）
   - IP: 内积（适合归一化向量）
   - COSINE: 余弦相似度

4. 💡 应用场景
   - RAG (检索增强生成)
   - 相似图片搜索
   - 推荐系统
   - 语义搜索
   - 异常检测
'''