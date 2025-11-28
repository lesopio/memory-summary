#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import time
from datetime import datetime
from typing import Dict, List, Optional


class MemoryManager:
    """
    简单的向量相似度计算（使用余弦相似度）
    在实际生产环境中，应该使用专业的向量数据库（如 Pinecone, Weaviate 等）
    """
    
    def __init__(self):
        self.memories: Dict[int, List[Dict]] = {}  # personaId -> memories list
        self.public_memories: List[Dict] = []  # 公共记忆
        self.decay_factor = 0.95  # 权重衰减因子
        self.max_memories_per_persona = 100  # 每个角色最大记忆数
    
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
        memory_obj = {
            'id': int(time.time() * 1000) + int(time.time() * 1000000 % 1000),
            'personaId': persona_id,
            'content': memory,
            'vector': self.vectorize(memory),
            'weight': 1.0,
            'timestamp': datetime.now().isoformat(),
            'isPublic': is_public,
            'accessCount': 0,
        }
        
        if is_public:
            self.public_memories.append(memory_obj)
            # 限制公共记忆数量
            if len(self.public_memories) > self.max_memories_per_persona:
                self.public_memories.pop(0)
        else:
            if persona_id not in self.memories:
                self.memories[persona_id] = []
            
            self.memories[persona_id].append(memory_obj)
            
            # 限制记忆数量
            if len(self.memories[persona_id]) > self.max_memories_per_persona:
                self.memories[persona_id].pop(0)
        
        return memory_obj
    
    def retrieve_memories(self, persona_id: int, query: str, limit: int = 5) -> List[Dict]:
        """检索相关记忆"""
        query_vector = self.vectorize(query)
        results = []
        
        # 检索角色专属记忆
        if persona_id in self.memories:
            for memory in self.memories[persona_id]:
                similarity = self.cosine_similarity(query_vector, memory['vector'])
                score = similarity * memory['weight']
                if score > 0.1:  # 阈值
                    result = memory.copy()
                    result['score'] = score
                    result['type'] = 'persona'
                    results.append(result)
        
        # 检索公共记忆
        for memory in self.public_memories:
            similarity = self.cosine_similarity(query_vector, memory['vector'])
            score = similarity * memory['weight']
            if score > 0.1:
                result = memory.copy()
                result['score'] = score
                result['type'] = 'public'
                results.append(result)
        
        # 按分数排序并返回top k
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    def apply_decay(self):
        """应用权重衰减"""
        # 对角色记忆应用衰减
        for persona_id in list(self.memories.keys()):
            memories = self.memories[persona_id]
            # 过滤掉权重过低的记忆
            self.memories[persona_id] = [
                memory for memory in memories
                if (memory.update({'weight': memory['weight'] * self.decay_factor}) or True) and memory['weight'] >= 0.1
            ]
        
        # 对公共记忆应用衰减
        self.public_memories = [
            memory for memory in self.public_memories
            if (memory.update({'weight': memory['weight'] * self.decay_factor}) or True) and memory['weight'] >= 0.1
        ]
    
    def merge_similar_memories(self, persona_id: int, threshold: float = 0.8):
        """合并相似记忆"""
        if persona_id not in self.memories:
            return
        
        memories = self.memories[persona_id]
        merged = []
        used = set()
        
        for i in range(len(memories)):
            if i in used:
                continue
            
            current = memories[i]
            similar = [current]
            
            for j in range(i + 1, len(memories)):
                if j in used:
                    continue
                
                similarity = self.cosine_similarity(current['vector'], memories[j]['vector'])
                if similarity >= threshold:
                    similar.append(memories[j])
                    used.add(j)
            
            # 合并相似记忆
            if len(similar) > 1:
                merged_content = '；'.join([m['content'] for m in similar])
                merged_weight = max([m['weight'] for m in similar])
                merged_memory = current.copy()
                merged_memory['content'] = merged_content
                merged_memory['weight'] = merged_weight
                merged_memory['vector'] = self.vectorize(merged_content)
                merged.append(merged_memory)
            else:
                merged.append(current)
            
            used.add(i)
        
        self.memories[persona_id] = merged
    
    def get_all_memories(self, persona_id: int) -> Dict:
        """获取所有记忆"""
        persona_memories = self.memories.get(persona_id, [])
        return {
            'persona': persona_memories,
            'public': self.public_memories,
        }
    
    def update_memory_weight(self, memory_id: int, persona_id: int, increment: float = 0.1):
        """更新记忆权重（当记忆被访问时）"""
        if persona_id in self.memories:
            for memory in self.memories[persona_id]:
                if memory['id'] == memory_id:
                    memory['weight'] = min(1.0, memory['weight'] + increment)
                    memory['accessCount'] = memory.get('accessCount', 0) + 1
                    return
        
        for memory in self.public_memories:
            if memory['id'] == memory_id:
                memory['weight'] = min(1.0, memory['weight'] + increment)
                memory['accessCount'] = memory.get('accessCount', 0) + 1
                return
