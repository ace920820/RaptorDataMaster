# Raptor 开发计划：集成Rerank模块以提升检索准确率

## 1. 背景和目标

### 1.1 当前检索流程
目前raptor使用纯向量检索方式进行文档检索，主要包含两种模式：
- 层次检索模式（collapse_tree=False）：自上而下逐层检索
- 扁平检索模式（collapse_tree=True）：直接在所有节点中检索

### 1.2 现有局限性
- 仅依赖向量相似度判断相关性
- 存在语义空间压缩导致的信息损失
- 难以捕捉细粒度的语义差异
- 对上下文理解有限

### 1.3 改进目标
通过引入rerank模块，在保持检索效率的同时提升检索准确率。

## 2. 技术方案

### 2.1 整体架构
```
查询 -> 向量检索(召回) -> Rerank(精排) -> 最终结果
```

### 2.2 Rerank模型选项

#### 方案A：轻量级方案
使用SentenceTransformers的CrossEncoder：
```python
from sentence_transformers import CrossEncoder
rerank_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-12-v2')
```

#### 方案B：高性能方案
使用专业的rerank模型如BGE-Reranker：
```python
from transformers import AutoModelForSequenceClassification, AutoTokenizer

class RerankModel:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-reranker-base")
        self.model = AutoModelForSequenceClassification.from_pretrained("BAAI/bge-reranker-base")
```

### 2.3 核心功能实现

#### Rerank基类定义
```python
class BaseRerankModel:
    def predict(self, query: str, passage: str) -> float:
        """计算query和passage的相关性分数"""
        raise NotImplementedError
        
    def batch_predict(self, query: str, passages: List[str]) -> List[float]:
        """批量计算相关性分数"""
        raise NotImplementedError
```

#### TreeRetriever改造
```python
class TreeRetriever:
    def retrieve(self, query: str, ...) -> str:
        # 1. 向量检索阶段
        selected_nodes, context = self.retrieve_information_collapse_tree(
            query, 
            top_k=self.top_k * 3,  # 扩大初筛范围
            max_tokens=max_tokens
        )
        
        # 2. Rerank阶段
        if self.rerank_model:
            candidates = [(node, node.text) for node in selected_nodes]
            reranked_results = self.rerank_model.rerank(
                query=query,
                candidates=candidates,
                top_k=self.top_k
            )
            selected_nodes = [node for node, _ in reranked_results]
```

## 3. 性能优化策略

### 3.1 批处理优化
```python
def batch_rerank(self, query: str, candidates: List[str], batch_size: int = 32) -> List[Tuple[str, float]]:
    """批量处理rerank请求"""
    scores = []
    for i in range(0, len(candidates), batch_size):
        batch = candidates[i:i + batch_size]
        batch_scores = self.rerank_model.batch_predict(query, batch)
        scores.extend(batch_scores)
    return scores
```

### 3.2 智能调用策略
```python
def should_rerank(self, scores: List[float], threshold: float = 0.1) -> bool:
    """判断是否需要rerank"""
    if not scores:
        return False
    # 只有当top结果分数差异小于阈值时才进行rerank
    return max(scores) - min(scores) < threshold
```

### 3.3 缓存机制
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_rerank_score(self, query: str, passage: str) -> float:
    """缓存rerank结果"""
    return self.rerank_model.predict(query, passage)
```

## 4. 配置项扩展

在TreeRetrieverConfig中添加rerank相关配置：
```python
class TreeRetrieverConfig:
    def __init__(self, 
                 rerank_enabled: bool = False,
                 rerank_model_name: str = "cross-encoder/ms-marco-MiniLM-L-12-v2",
                 rerank_batch_size: int = 32,
                 rerank_threshold: float = 0.1,
                 ...):
        self.rerank_enabled = rerank_enabled
        self.rerank_model_name = rerank_model_name
        self.rerank_batch_size = rerank_batch_size
        self.rerank_threshold = rerank_threshold
```

## 5. 开发计划

### 第一阶段：基础功能实现
1. 创建rerank模型基类和具体实现
2. 改造TreeRetriever，支持rerank流程
3. 扩展配置项
4. 添加基本的单元测试

### 第二阶段：性能优化
1. 实现批处理机制
2. 添加智能调用策略
3. 实现缓存机制
4. 进行性能测试和优化

### 第三阶段：稳定性保障
1. 完善异常处理
2. 添加详细的日志
3. 补充文档
4. 进行集成测试

## 6. 测试计划

### 6.1 单元测试
- Rerank模型的准确性测试
- 批处理功能测试
- 缓存机制测试
- 配置项测试

### 6.2 集成测试
- 端到端检索流程测试
- 性能压力测试
- 异常场景测试

### 6.3 效果评估
- 准确率评估（与原版对比）
- 延迟评估
- 资源消耗评估

## 7. 风险与应对策略

### 7.1 潜在风险
1. Rerank可能增加检索延迟
2. 模型加载可能增加内存占用
3. 批处理可能影响实时性

### 7.2 应对策略
1. 提供配置项控制是否启用rerank
2. 实现模型lazy loading
3. 支持配置批处理大小
4. 添加超时机制
5. 实现降级策略
