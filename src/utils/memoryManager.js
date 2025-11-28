// 简单的向量相似度计算（使用余弦相似度）
// 在实际生产环境中，应该使用专业的向量数据库（如 Pinecone, Weaviate 等）

class MemoryManager {
  constructor() {
    this.memories = new Map(); // personaId -> memories array
    this.publicMemories = []; // 公共记忆
    this.decayFactor = 0.95; // 权重衰减因子
    this.maxMemoriesPerPersona = 100; // 每个角色最大记忆数
  }

  // 简单的文本向量化（基于词频）
  vectorize(text) {
    const words = text.toLowerCase().match(/[\u4e00-\u9fa5]+|[a-zA-Z]+/g) || [];
    const vector = {};
    words.forEach(word => {
      vector[word] = (vector[word] || 0) + 1;
    });
    return vector;
  }

  // 计算余弦相似度
  cosineSimilarity(vec1, vec2) {
    const keys = new Set([...Object.keys(vec1), ...Object.keys(vec2)]);
    let dotProduct = 0;
    let norm1 = 0;
    let norm2 = 0;

    for (const key of keys) {
      const v1 = vec1[key] || 0;
      const v2 = vec2[key] || 0;
      dotProduct += v1 * v2;
      norm1 += v1 * v1;
      norm2 += v2 * v2;
    }

    if (norm1 === 0 || norm2 === 0) return 0;
    return dotProduct / (Math.sqrt(norm1) * Math.sqrt(norm2));
  }

  // 添加记忆
  addMemory(personaId, memory, isPublic = false) {
    const memoryObj = {
      id: Date.now() + Math.random(),
      personaId,
      content: memory,
      vector: this.vectorize(memory),
      weight: 1.0,
      timestamp: new Date().toISOString(),
      isPublic,
      accessCount: 0,
    };

    if (isPublic) {
      this.publicMemories.push(memoryObj);
      // 限制公共记忆数量
      if (this.publicMemories.length > this.maxMemoriesPerPersona) {
        this.publicMemories.shift();
      }
    } else {
      if (!this.memories.has(personaId)) {
        this.memories.set(personaId, []);
      }
      const personaMemories = this.memories.get(personaId);
      personaMemories.push(memoryObj);
      
      // 限制记忆数量
      if (personaMemories.length > this.maxMemoriesPerPersona) {
        personaMemories.shift();
      }
    }

    return memoryObj;
  }

  // 检索相关记忆
  retrieveMemories(personaId, query, limit = 5) {
    const queryVector = this.vectorize(query);
    const results = [];

    // 检索角色专属记忆
    if (this.memories.has(personaId)) {
      const personaMemories = this.memories.get(personaId);
      personaMemories.forEach(memory => {
        const similarity = this.cosineSimilarity(queryVector, memory.vector);
        const score = similarity * memory.weight;
        if (score > 0.1) { // 阈值
          results.push({ ...memory, score, type: 'persona' });
        }
      });
    }

    // 检索公共记忆
    this.publicMemories.forEach(memory => {
      const similarity = this.cosineSimilarity(queryVector, memory.vector);
      const score = similarity * memory.weight;
      if (score > 0.1) {
        results.push({ ...memory, score, type: 'public' });
      }
    });

    // 按分数排序并返回top k
    results.sort((a, b) => b.score - a.score);
    return results.slice(0, limit);
  }

  // 应用权重衰减
  applyDecay() {
    // 对角色记忆应用衰减
    this.memories.forEach((memories, personaId) => {
      memories.forEach(memory => {
        memory.weight *= this.decayFactor;
        // 移除权重过低的记忆
        if (memory.weight < 0.1) {
          const index = memories.indexOf(memory);
          if (index > -1) {
            memories.splice(index, 1);
          }
        }
      });
    });

    // 对公共记忆应用衰减
    this.publicMemories = this.publicMemories.filter(memory => {
      memory.weight *= this.decayFactor;
      return memory.weight >= 0.1;
    });
  }

  // 合并相似记忆
  mergeSimilarMemories(personaId, threshold = 0.8) {
    if (!this.memories.has(personaId)) return;

    const memories = this.memories.get(personaId);
    const merged = [];
    const used = new Set();

    for (let i = 0; i < memories.length; i++) {
      if (used.has(i)) continue;

      const current = memories[i];
      const similar = [current];

      for (let j = i + 1; j < memories.length; j++) {
        if (used.has(j)) continue;

        const similarity = this.cosineSimilarity(current.vector, memories[j].vector);
        if (similarity >= threshold) {
          similar.push(memories[j]);
          used.add(j);
        }
      }

      // 合并相似记忆
      if (similar.length > 1) {
        const mergedContent = similar.map(m => m.content).join('；');
        const mergedWeight = Math.max(...similar.map(m => m.weight));
        merged.push({
          ...current,
          content: mergedContent,
          weight: mergedWeight,
          vector: this.vectorize(mergedContent),
        });
      } else {
        merged.push(current);
      }

      used.add(i);
    }

    this.memories.set(personaId, merged);
  }

  // 获取所有记忆
  getAllMemories(personaId) {
    const personaMemories = this.memories.get(personaId) || [];
    return {
      persona: personaMemories,
      public: this.publicMemories,
    };
  }

  // 更新记忆权重（当记忆被访问时）
  updateMemoryWeight(memoryId, personaId, increment = 0.1) {
    if (this.memories.has(personaId)) {
      const memory = this.memories.get(personaId).find(m => m.id === memoryId);
      if (memory) {
        memory.weight = Math.min(1.0, memory.weight + increment);
        memory.accessCount++;
      }
    }

    const publicMemory = this.publicMemories.find(m => m.id === memoryId);
    if (publicMemory) {
      publicMemory.weight = Math.min(1.0, publicMemory.weight + increment);
      publicMemory.accessCount++;
    }
  }
}

export default MemoryManager;

