#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
记忆管理器 v2 - 集成数据库持久化
支持向量化存储、语义检索、权重衰减和数据库持久化
"""

import re
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database import get_db

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    记忆管理器 - 支持数据库持久化
    使用简单的向量相似度计算（余弦相似度）
    在实际生产环境中，应该使用专业的向量数据库（如 Pinecone, Weaviate 等）
    """
    
    def __init__(self, use_database: bool = True):
        """初始化记忆管理器"""
        self.use_database = use_database
        self.db = get_db() if use_database else None
        
        # 内存缓存（用于快速访问）
        self.memory_cache: Dict[int, List[Dict]] = {}
        self.cache_timeout = 60  # 缓存超时时间（秒）
        self.last_cache_update = {}
        
        self.decay_factor = 0.95  # 权重衰减因子
        self.max_memories_per_persona = 100  # 每个角色最大记忆数
        
        # 如果使用数据库，加载现有记忆到缓存
        if self.use_database:
            self._load_cache()
    
    def _load_cache(self):
        """从数据库加载记忆到缓存"""
        try:
            all_memories = self.db.get_memories()
            for memory in all_memories:
                persona_id = memory['persona_id']
                if persona_id not in self.memory_cache:
                    self.memory_cache[persona_id] = []
                
                # 解析向量
                vector = json.loads(memory['vector']) if memory['vector'] else {}
                
                memory_obj = {
                    'id': memory['id'],
                    'personaId': persona_id,
                    'content': memory['content'],
                    'vector': vector,
                    'weight': memory['weight'],
                    'timestamp': memory['created_at'],
                    'isPublic': bool(memory['is_public']),
                    'accessCount': 0,
                }
                self.memory_cache[persona_id].append(memory_obj)
            
            logger.info(f'从数据库加载了 {len(all_memories)} 条记忆')
        except Exception as e:
            logger.error(f'加载缓存失败: {e}')
    
    def vectorize(self, text: str) -> Dict[str, int]:
        """简单的文本向量化（基于词频）"""
        # 匹配中文字符和英文单词
        words = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z]+', text.lower())
        vector = {}
        for word in words:
            vector[word] = vector.get(word, 0) + 1
        return vector
    
    def cosine_similarity(self, vec1: Dict[str, int], vec2: Dict[str, int]) -> float:
        """计算余弦相似度"""
        keys = set(vec1.keys()) | set(vec2.keys())
        dot_product = 0
        norm1 = 0
        norm2 = 0
        
        for key in keys:
            v1 = vec1.get(key, 0)
            v2 = vec2.get(key, 0)
            dot_product += v1 * v2
            norm1 += v1 * v1
            norm2 += v2 * v2
        
        if norm1 == 0 or norm2 == 0:
            return 0
        
        return dot_product / ((norm1 ** 0.5) * (norm2 ** 0.5))
    
    def add_memory(self, persona_id: int, memory: str, is_public: bool = False) -> Dict:
        """添加记忆"""
        vector = self.vectorize(memory)
        
        memory_obj = {
            'personaId': persona_id,
            'content': memory,
            'vector': vector,
            'weight': 1.0,
            'timestamp': datetime.now().isoformat(),
            'isPublic': is_public,
            'accessCount': 0,
        }
        
        # 保存到数据库
        if self.use_database:
            try:
                # 将向量字典转换为 JSON 字符串
                vector_data = vector if vector else {}
                memory_id = self.db.add_memory(
                    persona_id=persona_id,
                    content=memory,
                    vector=vector_data,  # 传递字典,数据库模块会处理序列化
                    weight=1.0,
                    is_public=is_public
                )
                memory_obj['id'] = memory_id
                logger.info(f'记忆已保存到数据库: ID={memory_id}')
            except Exception as e:
                logger.error(f'保存记忆到数据库失败: {e}')
                memory_obj['id'] = int(time.time() * 1000000)
        else:
            memory_obj['id'] = int(time.time() * 1000000)
        
        # 更新缓存
        if persona_id not in self.memory_cache:
            self.memory_cache[persona_id] = []
        
        self.memory_cache[persona_id].append(memory_obj)
        
        # 限制记忆数量
        if len(self.memory_cache[persona_id]) > self.max_memories_per_persona:
            removed = self.memory_cache[persona_id].pop(0)
            if self.use_database and 'id' in removed:
                try:
                    self.db.delete_memory(removed['id'])
                except Exception as e:
                    logger.error(f'删除旧记忆失败: {e}')
        
        return memory_obj
    
    def retrieve_memories(self, persona_id: int, query: str, limit: int = 5) -> List[Dict]:
        """检索相关记忆"""
        query_vector = self.vectorize(query)
        results = []
        
        # 检索角色专属记忆
        if persona_id in self.memory_cache:
            for memory in self.memory_cache[persona_id]:
                if memory['isPublic']:
                    continue  # 公共记忆单独处理
                
                similarity = self.cosine_similarity(query_vector, memory['vector'])
                score = similarity * memory['weight']
                if score > 0.1:  # 阈值
                    result = memory.copy()
                    result['score'] = score
                    result['type'] = 'persona'
                    results.append(result)
                    
                    # 增加访问计数和权重
                    memory['accessCount'] += 1
                    memory['weight'] = min(memory['weight'] + 0.1, 2.0)
        
        # 检索公共记忆
        for pid, memories in self.memory_cache.items():
            for memory in memories:
                if not memory['isPublic']:
                    continue
                
                similarity = self.cosine_similarity(query_vector, memory['vector'])
                score = similarity * memory['weight']
                if score > 0.1:
                    result = memory.copy()
                    result['score'] = score
                    result['type'] = 'public'
                    results.append(result)
                    
                    # 增加访问计数和权重
                    memory['accessCount'] += 1
                    memory['weight'] = min(memory['weight'] + 0.1, 2.0)
        
        # 按相关度排序并限制数量
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    def get_all_memories(self, persona_id: int, include_public: bool = True) -> List[Dict]:
        """获取所有记忆（用于显示）"""
        results = []
        
        # 获取角色记忆
        if persona_id in self.memory_cache:
            for memory in self.memory_cache[persona_id]:
                if memory['isPublic'] and not include_public:
                    continue
                result = memory.copy()
                result['type'] = 'public' if memory['isPublic'] else 'persona'
                results.append(result)
        
        # 获取公共记忆
        if include_public:
            for pid, memories in self.memory_cache.items():
                if pid == persona_id:
                    continue
                for memory in memories:
                    if memory['isPublic']:
                        result = memory.copy()
                        result['type'] = 'public'
                        results.append(result)
        
        # 按时间倒序排序
        results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return results
    
    def update_memory(self, memory_id: int, content: str = None) -> bool:
        """更新记忆内容"""
        try:
            if self.use_database:
                if content:
                    vector = self.vectorize(content)
                    vector_data = vector if vector else {}
                    self.db.update_memory(
                        memory_id=memory_id,
                        content=content,
                        vector=vector_data
                    )
                
                # 更新缓存
                for persona_id, memories in self.memory_cache.items():
                    for memory in memories:
                        if memory.get('id') == memory_id:
                            if content:
                                memory['content'] = content
                                memory['vector'] = self.vectorize(content)
                            return True
            
            return False
        except Exception as e:
            logger.error(f'更新记忆失败: {e}')
            return False
    
    def delete_memory(self, memory_id: int) -> bool:
        """删除记忆"""
        try:
            if self.use_database:
                self.db.delete_memory(memory_id)
            
            # 从缓存中删除
            for persona_id, memories in self.memory_cache.items():
                for i, memory in enumerate(memories):
                    if memory.get('id') == memory_id:
                        memories.pop(i)
                        logger.info(f'记忆已删除: ID={memory_id}')
                        return True
            
            return False
        except Exception as e:
            logger.error(f'删除记忆失败: {e}')
            return False
    
    def apply_decay(self):
        """应用权重衰减"""
        logger.info('开始应用权重衰减...')
        
        for persona_id, memories in self.memory_cache.items():
            for memory in memories:
                memory['weight'] *= self.decay_factor
                
                # 更新数据库
                if self.use_database and 'id' in memory:
                    try:
                        self.db.update_memory_weight(memory['id'], memory['weight'])
                    except Exception as e:
                        logger.error(f'更新权重失败: {e}')
        
        # 删除权重过低的记忆
        removed_count = 0
        for persona_id, memories in list(self.memory_cache.items()):
            to_remove = []
            for i, memory in enumerate(memories):
                if memory['weight'] < 0.1:
                    to_remove.append(i)
                    if self.use_database and 'id' in memory:
                        try:
                            self.db.delete_memory(memory['id'])
                        except Exception as e:
                            logger.error(f'删除低权重记忆失败: {e}')
            
            # 从后向前删除，避免索引错乱
            for i in reversed(to_remove):
                memories.pop(i)
                removed_count += 1
        
        logger.info(f'权重衰减完成，删除了 {removed_count} 条低权重记忆')
    
    def merge_similar_memories(self, threshold: float = 0.8):
        """合并相似记忆"""
        logger.info('开始合并相似记忆...')
        merged_count = 0
        
        for persona_id, memories in self.memory_cache.items():
            i = 0
            while i < len(memories):
                j = i + 1
                while j < len(memories):
                    similarity = self.cosine_similarity(memories[i]['vector'], memories[j]['vector'])
                    
                    if similarity > threshold:
                        # 合并记忆：保留权重较高的，删除另一个
                        if memories[i]['weight'] >= memories[j]['weight']:
                            to_remove = memories.pop(j)
                            memories[i]['weight'] += to_remove['weight'] * 0.5
                        else:
                            to_remove = memories.pop(i)
                            memories[j]['weight'] += to_remove['weight'] * 0.5
                            i -= 1
                            break
                        
                        # 从数据库删除
                        if self.use_database and 'id' in to_remove:
                            try:
                                self.db.delete_memory(to_remove['id'])
                            except Exception as e:
                                logger.error(f'删除合并记忆失败: {e}')
                        
                        merged_count += 1
                    else:
                        j += 1
                
                i += 1
        
        logger.info(f'记忆合并完成，合并了 {merged_count} 对相似记忆')
    
    def export_memories(self) -> Dict:
        """导出所有记忆"""
        if self.use_database:
            return self.db.export_all_data()
        else:
            return {
                'memories': self.memory_cache,
                'export_time': datetime.now().isoformat()
            }
    
    def import_memories(self, data: Dict):
        """导入记忆数据"""
        if self.use_database:
            self.db.import_data(data)
            self._load_cache()
        else:
            if 'memories' in data:
                self.memory_cache = data['memories']


if __name__ == '__main__':
    # 测试记忆管理器
    logging.basicConfig(level=logging.INFO)
    
    manager = MemoryManager(use_database=True)
    
    # 添加测试记忆
    manager.add_memory(1, '用户喜欢吃苹果', is_public=False)
    manager.add_memory(1, '用户住在北京', is_public=False)
    manager.add_memory(1, 'Python 是一种编程语言', is_public=True)
    
    # 检索记忆
    results = manager.retrieve_memories(1, '用户喜欢什么水果')
    print(f'检索结果: {len(results)} 条')
    for r in results:
        print(f'  - {r["content"]} (相关度: {r["score"]:.2f})')
    
    # 获取所有记忆
    all_memories = manager.get_all_memories(1)
    print(f'\n所有记忆: {len(all_memories)} 条')
    for m in all_memories:
        print(f'  - [{m["type"]}] {m["content"]}')
    
    print('\n测试完成')
