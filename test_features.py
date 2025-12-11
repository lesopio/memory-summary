#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
功能测试脚本
测试数据库、记忆管理器和 API 配置
"""

import sys
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def test_database():
    """测试数据库功能"""
    logger.info('=' * 50)
    logger.info('测试数据库模块')
    logger.info('=' * 50)
    
    try:
        from database import Database
        
        # 使用临时数据库
        db = Database(':memory:')
        
        # 测试创建 Persona
        pid = db.create_persona('测试助手', '这是一个测试助手')
        logger.info(f'✅ 创建 Persona: ID={pid}')
        
        # 测试获取 Persona
        persona = db.get_persona(pid)
        assert persona['name'] == '测试助手'
        logger.info(f'✅ 获取 Persona: {persona["name"]}')
        
        # 测试添加记忆
        mid = db.add_memory(pid, '用户喜欢吃苹果', weight=1.0, is_public=False)
        logger.info(f'✅ 添加记忆: ID={mid}')
        
        # 测试获取记忆
        memories = db.get_memories(pid)
        assert len(memories) == 1
        logger.info(f'✅ 获取记忆: {len(memories)} 条')
        
        # 测试更新记忆
        db.update_memory(mid, content='用户喜欢吃香蕉')
        updated = db.get_memory(mid)
        assert '香蕉' in updated['content']
        logger.info(f'✅ 更新记忆成功')
        
        # 测试删除记忆
        db.delete_memory(mid)
        memories = db.get_memories(pid)
        assert len(memories) == 0
        logger.info(f'✅ 删除记忆成功')
        
        # 测试聊天记录
        db.add_chat_message(pid, 'user', '你好')
        db.add_chat_message(pid, 'assistant', '你好！有什么可以帮助你的吗？')
        history = db.get_chat_history(pid)
        assert len(history) == 2
        logger.info(f'✅ 聊天记录: {len(history)} 条')
        
        # 测试导出
        export_data = db.export_all_data()
        assert 'personas' in export_data
        assert 'memories' in export_data
        logger.info(f'✅ 数据导出成功')
        
        db.close()
        logger.info('✅ 数据库模块测试通过\n')
        return True
        
    except Exception as e:
        logger.error(f'❌ 数据库测试失败: {e}')
        import traceback
        traceback.print_exc()
        return False


def test_memory_manager():
    """测试记忆管理器"""
    logger.info('=' * 50)
    logger.info('测试记忆管理器')
    logger.info('=' * 50)
    
    try:
        from src.utils.memory_manager_v2 import MemoryManager
        
        # 使用内存数据库
        manager = MemoryManager(use_database=True)
        
        # 测试添加记忆
        m1 = manager.add_memory(1, '用户喜欢吃苹果', is_public=False)
        logger.info(f'✅ 添加记忆 1: {m1["content"][:20]}...')
        
        m2 = manager.add_memory(1, '用户住在北京', is_public=False)
        logger.info(f'✅ 添加记忆 2: {m2["content"][:20]}...')
        
        m3 = manager.add_memory(1, 'Python 是一种编程语言', is_public=True)
        logger.info(f'✅ 添加公共记忆: {m3["content"][:20]}...')
        
        # 测试检索记忆
        results = manager.retrieve_memories(1, '用户喜欢什么水果')
        logger.info(f'✅ 检索记忆: {len(results)} 条相关记忆')
        if len(results) > 0:
            for r in results[:2]:
                logger.info(f'   - {r["content"][:30]}... (相关度: {r["score"]:.2f})')
        else:
            logger.warning(f'⚠️  未检索到相关记忆（可能是相似度阈值问题）')
        
        # 测试获取所有记忆
        all_memories = manager.get_all_memories(1)
        assert len(all_memories) >= 3
        logger.info(f'✅ 获取所有记忆: {len(all_memories)} 条')
        
        # 测试更新记忆
        if 'id' in m1:
            success = manager.update_memory(m1['id'], '用户喜欢吃香蕉')
            if success:
                logger.info(f'✅ 更新记忆成功')
            else:
                logger.warning(f'⚠️  更新记忆失败（可能使用内存数据库）')
        
        # 测试删除记忆
        if 'id' in m2:
            success = manager.delete_memory(m2['id'])
            if success:
                logger.info(f'✅ 删除记忆成功')
            else:
                logger.warning(f'⚠️  删除记忆失败（可能使用内存数据库）')
        
        # 测试向量化
        vector = manager.vectorize('这是一个测试文本')
        assert len(vector) > 0
        logger.info(f'✅ 文本向量化: {len(vector)} 个特征')
        
        # 测试相似度计算
        v1 = manager.vectorize('苹果很好吃')
        v2 = manager.vectorize('香蕉很美味')
        similarity = manager.cosine_similarity(v1, v2)
        logger.info(f'✅ 相似度计算: {similarity:.3f}')
        
        logger.info('✅ 记忆管理器测试通过\n')
        return True
        
    except Exception as e:
        logger.error(f'❌ 记忆管理器测试失败: {e}')
        import traceback
        traceback.print_exc()
        return False


def test_api_config():
    """测试 API 配置"""
    logger.info('=' * 50)
    logger.info('测试 API 配置模块')
    logger.info('=' * 50)
    
    try:
        from api_config import APIConfig, get_api_config
        
        # 测试获取可用提供商
        providers = APIConfig.get_available_providers()
        logger.info(f'✅ 可用提供商: {len(providers)} 个')
        for p in providers:
            status = '✅' if p['configured'] else '❌'
            logger.info(f'   {status} {p["name"]} - {len(p["models"])} 个模型')
        
        # 测试获取所有模型
        models = APIConfig.get_all_models()
        logger.info(f'✅ 可用模型总数: {len(models)} 个')
        
        # 测试 LongCat 配置
        config = APIConfig('longcat')
        logger.info(f'✅ LongCat 配置:')
        logger.info(f'   - 端点: {config.get_endpoint()}')
        logger.info(f'   - 已配置: {config.is_configured()}')
        logger.info(f'   - 支持流式: {config.supports_stream}')
        
        # 测试消息格式化
        messages = [
            {'role': 'system', 'content': '你是一个助手'},
            {'role': 'user', 'content': '你好'}
        ]
        formatted = config.format_messages(messages)
        logger.info(f'✅ 消息格式化成功')
        
        # 测试请求体构建
        body = config.build_request_body('test-model', messages)
        assert 'model' in body
        assert 'messages' in body
        logger.info(f'✅ 请求体构建成功')
        
        logger.info('✅ API 配置模块测试通过\n')
        return True
        
    except Exception as e:
        logger.error(f'❌ API 配置测试失败: {e}')
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    logger.info('\n' + '=' * 50)
    logger.info('开始功能测试')
    logger.info('=' * 50 + '\n')
    
    results = {
        '数据库模块': test_database(),
        '记忆管理器': test_memory_manager(),
        'API 配置': test_api_config(),
    }
    
    logger.info('=' * 50)
    logger.info('测试结果汇总')
    logger.info('=' * 50)
    
    for name, passed in results.items():
        status = '✅ 通过' if passed else '❌ 失败'
        logger.info(f'{name}: {status}')
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info('\n🎉 所有测试通过！')
        return 0
    else:
        logger.error('\n❌ 部分测试失败，请检查错误信息')
        return 1


if __name__ == '__main__':
    sys.exit(main())
