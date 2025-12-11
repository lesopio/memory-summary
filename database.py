#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SQLite 数据库管理模块
用于持久化存储 Personas、聊天记录和记忆数据
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# 数据库文件路径
DB_PATH = Path(__file__).parent / 'memory_data.db'


class Database:
    """数据库管理类"""
    
    def __init__(self, db_path: str = None):
        """初始化数据库连接"""
        self.db_path = db_path or str(DB_PATH)
        self.conn = None
        self.init_database()
    
    def get_connection(self):
        """获取数据库连接"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # 使用字典式访问
        return self.conn
    
    def init_database(self):
        """初始化数据库表结构"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 创建 Personas 表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS personas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建聊天会话表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                persona_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                model TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (persona_id) REFERENCES personas(id) ON DELETE CASCADE
            )
        ''')
        
        # 创建记忆表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                persona_id INTEGER,
                content TEXT NOT NULL,
                vector TEXT,
                weight REAL DEFAULT 1.0,
                is_public BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (persona_id) REFERENCES personas(id) ON DELETE CASCADE
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_persona ON chat_sessions(persona_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_memory_persona ON memories(persona_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_memory_public ON memories(is_public)')
        
        conn.commit()
        logger.info(f'数据库初始化完成: {self.db_path}')
    
    # ==================== Persona 操作 ====================
    
    def get_all_personas(self) -> List[Dict]:
        """获取所有 Persona"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM personas ORDER BY id')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_persona(self, persona_id: int) -> Optional[Dict]:
        """获取单个 Persona"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM personas WHERE id = ?', (persona_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def create_persona(self, name: str, description: str = '') -> int:
        """创建新 Persona"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO personas (name, description) VALUES (?, ?)',
            (name, description)
        )
        conn.commit()
        return cursor.lastrowid
    
    def update_persona(self, persona_id: int, name: str = None, description: str = None):
        """更新 Persona"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if name is not None:
            updates.append('name = ?')
            params.append(name)
        if description is not None:
            updates.append('description = ?')
            params.append(description)
        
        if updates:
            updates.append('updated_at = CURRENT_TIMESTAMP')
            params.append(persona_id)
            cursor.execute(
                f'UPDATE personas SET {", ".join(updates)} WHERE id = ?',
                params
            )
            conn.commit()
    
    def delete_persona(self, persona_id: int):
        """删除 Persona（级联删除相关数据）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM personas WHERE id = ?', (persona_id,))
        conn.commit()
    
    # ==================== 聊天记录操作 ====================
    
    def get_chat_history(self, persona_id: int, limit: int = 50) -> List[Dict]:
        """获取聊天历史"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM chat_sessions WHERE persona_id = ? ORDER BY created_at DESC LIMIT ?',
            (persona_id, limit)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in reversed(rows)]  # 按时间正序返回
    
    def add_chat_message(self, persona_id: int, role: str, content: str, model: str = None) -> int:
        """添加聊天消息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO chat_sessions (persona_id, role, content, model) VALUES (?, ?, ?, ?)',
            (persona_id, role, content, model)
        )
        conn.commit()
        return cursor.lastrowid
    
    def clear_chat_history(self, persona_id: int):
        """清空聊天历史"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM chat_sessions WHERE persona_id = ?', (persona_id,))
        conn.commit()
    
    # ==================== 记忆操作 ====================
    
    def get_memories(self, persona_id: int = None, include_public: bool = True) -> List[Dict]:
        """获取记忆列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if persona_id is None:
            # 获取所有记忆
            cursor.execute('SELECT * FROM memories ORDER BY created_at DESC')
        elif include_public:
            # 获取指定 Persona 的记忆 + 公共记忆
            cursor.execute(
                'SELECT * FROM memories WHERE persona_id = ? OR is_public = 1 ORDER BY created_at DESC',
                (persona_id,)
            )
        else:
            # 仅获取指定 Persona 的私有记忆
            cursor.execute(
                'SELECT * FROM memories WHERE persona_id = ? AND is_public = 0 ORDER BY created_at DESC',
                (persona_id,)
            )
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_memory(self, memory_id: int) -> Optional[Dict]:
        """获取单条记忆"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM memories WHERE id = ?', (memory_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def add_memory(self, persona_id: int, content: str, vector: List[float] = None, 
                   weight: float = 1.0, is_public: bool = False) -> int:
        """添加新记忆"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        vector_json = json.dumps(vector) if vector else None
        
        cursor.execute(
            'INSERT INTO memories (persona_id, content, vector, weight, is_public) VALUES (?, ?, ?, ?, ?)',
            (persona_id, content, vector_json, weight, int(is_public))
        )
        conn.commit()
        return cursor.lastrowid
    
    def update_memory(self, memory_id: int, content: str = None, vector: List[float] = None, 
                      weight: float = None, is_public: bool = None):
        """更新记忆"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if content is not None:
            updates.append('content = ?')
            params.append(content)
        if vector is not None:
            updates.append('vector = ?')
            params.append(json.dumps(vector))
        if weight is not None:
            updates.append('weight = ?')
            params.append(weight)
        if is_public is not None:
            updates.append('is_public = ?')
            params.append(int(is_public))
        
        if updates:
            updates.append('updated_at = CURRENT_TIMESTAMP')
            params.append(memory_id)
            cursor.execute(
                f'UPDATE memories SET {", ".join(updates)} WHERE id = ?',
                params
            )
            conn.commit()
    
    def delete_memory(self, memory_id: int):
        """删除记忆"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM memories WHERE id = ?', (memory_id,))
        conn.commit()
    
    def update_memory_weight(self, memory_id: int, weight: float):
        """更新记忆权重"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE memories SET weight = ? WHERE id = ?', (weight, memory_id))
        conn.commit()
    
    def apply_weight_decay(self, decay_factor: float = 0.95):
        """对所有记忆应用权重衰减"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE memories SET weight = weight * ?', (decay_factor,))
        conn.commit()
        
        # 删除权重过低的记忆
        cursor.execute('DELETE FROM memories WHERE weight < 0.1')
        deleted = cursor.rowcount
        conn.commit()
        
        logger.info(f'权重衰减完成，删除了 {deleted} 条低权重记忆')
        return deleted
    
    # ==================== 数据导出/导入 ====================
    
    def export_all_data(self) -> Dict[str, Any]:
        """导出所有数据为 JSON"""
        return {
            'personas': self.get_all_personas(),
            'memories': self.get_memories(),
            'export_time': datetime.now().isoformat()
        }
    
    def import_data(self, data: Dict[str, Any]):
        """从 JSON 导入数据"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 导入 Personas
        if 'personas' in data:
            for persona in data['personas']:
                cursor.execute(
                    'INSERT OR REPLACE INTO personas (id, name, description) VALUES (?, ?, ?)',
                    (persona.get('id'), persona.get('name'), persona.get('description', ''))
                )
        
        # 导入记忆
        if 'memories' in data:
            for memory in data['memories']:
                cursor.execute(
                    'INSERT OR REPLACE INTO memories (id, persona_id, content, vector, weight, is_public) VALUES (?, ?, ?, ?, ?, ?)',
                    (
                        memory.get('id'),
                        memory.get('persona_id'),
                        memory.get('content'),
                        memory.get('vector'),
                        memory.get('weight', 1.0),
                        memory.get('is_public', 0)
                    )
                )
        
        conn.commit()
        logger.info('数据导入完成')
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None


# 全局数据库实例
_db_instance = None

def get_db() -> Database:
    """获取全局数据库实例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


if __name__ == '__main__':
    # 测试数据库功能
    logging.basicConfig(level=logging.INFO)
    
    db = Database(':memory:')  # 使用内存数据库测试
    
    # 创建测试 Persona
    pid = db.create_persona('测试助手', '这是一个测试')
    print(f'创建 Persona ID: {pid}')
    
    # 添加测试记忆
    mid = db.add_memory(pid, '这是一条测试记忆', weight=1.0, is_public=False)
    print(f'创建记忆 ID: {mid}')
    
    # 查询记忆
    memories = db.get_memories(pid)
    print(f'记忆数量: {len(memories)}')
    print(f'记忆内容: {memories}')
    
    # 导出数据
    export_data = db.export_all_data()
    print(f'导出数据: {json.dumps(export_data, ensure_ascii=False, indent=2)}')
    
    db.close()
    print('数据库测试完成')
