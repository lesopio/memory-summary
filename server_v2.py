#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LongCat Chat Server v2 - 增强版
支持数据库持久化、记忆管理、流式输出
"""

import os
import json
import requests
import logging
from datetime import datetime
from threading import Thread
import time
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from src.utils.memory_manager_v2 import MemoryManager
from database import get_db

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# 初始化 Flask 应用
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "supports_credentials": True}})

PORT = 3001

# 初始化数据库和记忆管理器
db = get_db()
memory_manager = MemoryManager(use_database=True)

# 定期应用权重衰减（每小时）
def apply_decay_periodically():
    while True:
        time.sleep(60 * 60)  # 每小时
        memory_manager.apply_decay()
        logger.info('记忆权重衰减已应用')

# 启动衰减线程
decay_thread = Thread(target=apply_decay_periodically, daemon=True)
decay_thread.start()

# LongCat API 配置
LONGCAT_API_BASE = 'https://api.longcat.chat/openai'
DEFAULT_MODEL = 'LongCat-Flash-Chat'
THINKING_MODEL = 'LongCat-Flash-Thinking'
API_TIMEOUT = int(os.getenv('LONGCAT_API_TIMEOUT_MS', 30000)) / 1000

# 存储数据
chat_sessions = {}  # 存储每个 persona 的聊天记录（内存）
current_models = {}  # 存储每个 persona 当前使用的模型

# 初始化默认 Personas（如果数据库为空）
def init_default_personas():
    """初始化默认 Personas"""
    existing = db.get_all_personas()
    if not existing:
        default_personas = [
            {'name': '学术助手', 'description': '帮助进行学术研究和写作'},
            {'name': '创意写作', 'description': '协助创意写作和故事创作'},
            {'name': '技术支持', 'description': '提供技术问题解答'},
            {'name': '翻译助手', 'description': '多语言翻译服务'},
        ]
        for p in default_personas:
            db.create_persona(p['name'], p['description'])
        logger.info('已创建默认 Personas')

init_default_personas()


# ==================== API 路由 ====================

# 获取 Persona 列表
@app.route('/personas', methods=['GET'])
def get_personas():
    personas = db.get_all_personas()
    return jsonify(personas)


# 创建新 Persona
@app.route('/personas', methods=['POST'])
def create_persona():
    data = request.get_json()
    name = data.get('name')
    description = data.get('description', '')
    
    if not name:
        return jsonify({'error': '缺少 Persona 名称'}), 400
    
    persona_id = db.create_persona(name, description)
    return jsonify({'id': persona_id, 'name': name, 'description': description})


# 切换模型
@app.route('/switch-model', methods=['POST'])
def switch_model():
    data = request.get_json()
    persona = data.get('persona')
    model = data.get('model')
    
    if not persona or not model:
        return jsonify({'error': '缺少必要参数'}), 400
    
    valid_models = [DEFAULT_MODEL, THINKING_MODEL]
    if model not in valid_models:
        return jsonify({'error': f'无效的模型名称。支持的模型: {", ".join(valid_models)}'}), 400
    
    current_models[persona] = model
    return jsonify({'success': True, 'model': model})


# 调用 LongCat API
def call_longcat_api(model, messages, stream=True):
    api_key = os.getenv('LONGCAT_API_KEY', '')
    
    if not api_key:
        raise Exception('LONGCAT_API_KEY 未设置。请在 .env 文件中设置 API 密钥，或设置环境变量 LONGCAT_API_KEY。')
    
    request_body = {
        'model': model,
        'messages': messages,
        'temperature': 0.7,
    }
    
    if stream:
        request_body['stream'] = True
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
    }
    
    if stream:
        headers['Accept'] = 'text/event-stream, application/json'
    
    api_url = f'{LONGCAT_API_BASE}/v1/chat/completions'
    
    try:
        response = requests.post(
            api_url,
            json=request_body,
            headers=headers,
            timeout=API_TIMEOUT,
            stream=stream
        )
    except requests.Timeout:
        raise Exception(f'API调用超时（{API_TIMEOUT * 1000:.0f}ms）')
    except Exception as err:
        raise err
    
    if response.status_code != 200:
        error_text = response.text
        error_message = f'API调用失败: {response.status_code}'
        try:
            error_data = response.json()
            if 'error' in error_data:
                error_info = error_data['error']
                if isinstance(error_info, dict):
                    error_message += f' - {error_info.get("message", error_info.get("code", "未知错误"))}'
                else:
                    error_message += f' - {error_info}'
            if response.status_code == 401:
                error_message += '\n提示：请检查 LONGCAT_API_KEY 是否正确设置。'
        except:
            error_message += f' - {error_text}'
        raise Exception(error_message)
    
    return response


# 生成记忆摘要
def generate_memory_summary(persona_id, conversation):
    try:
        persona_obj = db.get_persona(persona_id)
        
        conversation_text = '\n'.join([f"{msg['role']}: {msg['content']}" for msg in conversation])
        summary_prompt = f"""请为以下对话生成一个简洁的记忆摘要（1-2句话），重点关注重要信息和关键点：

对话内容：
{conversation_text}

记忆摘要："""
        
        messages = [
            {'role': 'system', 'content': '你是一个专业的记忆摘要生成助手。请生成简洁、准确的中文摘要。'},
            {'role': 'user', 'content': summary_prompt},
        ]
        
        response = call_longcat_api(DEFAULT_MODEL, messages, stream=False)
        data = response.json()
        return data.get('choices', [{}])[0].get('message', {}).get('content', '')
    except Exception as error:
        logger.error(f'生成记忆摘要失败: {error}')
        # 如果API调用失败，使用简单的摘要方法
        last_messages = conversation[-4:]
        return ' | '.join([msg['content'] for msg in last_messages])[:200]


# 聊天接口 - 流式响应
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    persona = data.get('persona')
    message = data.get('message')
    model = data.get('model')
    
    if not persona or not message:
        return jsonify({'error': '缺少必要参数'}), 400
    
    try:
        # 验证并选择模型
        valid_models = [DEFAULT_MODEL, THINKING_MODEL]
        selected_model = model or current_models.get(persona, DEFAULT_MODEL)
        if selected_model not in valid_models:
            selected_model = DEFAULT_MODEL
        
        persona_obj = db.get_persona(persona)
        
        # 检索相关记忆
        relevant_memories = memory_manager.retrieve_memories(persona, message, 3)
        memory_context = ''
        if relevant_memories:
            memory_list = '\n'.join([
                f"- {m['content']} ({'角色记忆' if m.get('type') == 'persona' else '公共记忆'})"
                for m in relevant_memories
            ])
            memory_context = f'相关记忆：\n{memory_list}\n\n'
        
        # 构建消息历史
        if persona not in chat_sessions:
            chat_sessions[persona] = []
        
        # 添加系统提示词
        system_content = f"{persona_obj.get('description', '') if persona_obj else ''}\n\n{memory_context}请根据以上信息和记忆，自然地回应用户。"
        system_message = {
            'role': 'system',
            'content': system_content,
        }
        
        # 构建完整消息列表
        messages = [system_message] + chat_sessions[persona][-10:] + [{'role': 'user', 'content': message}]
        
        # 保存用户消息
        chat_sessions[persona].append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat(),
        })
        
        # 保存到数据库
        db.add_chat_message(persona, 'user', message, selected_model)
        
        # 调用 LongCat API
        logger.info(f'[Chat] 调用 API - Persona: {persona}, Model: {selected_model}')
        api_response = call_longcat_api(selected_model, messages, stream=True)
        
        logger.info(f'[Chat] API 响应状态: {api_response.status_code}')
        
        # 生成流式响应
        def generate():
            full_response = ''
            buffer = ''
            
            try:
                for line_bytes in api_response.iter_lines():
                    if not line_bytes:
                        continue
                    
                    line = line_bytes.decode('utf-8') if isinstance(line_bytes, bytes) else line_bytes
                    
                    if not line.strip():
                        continue
                    
                    # 处理 SSE 格式: data: {...}
                    if line.startswith('data: '):
                        data_str = line[6:].strip()
                        
                        if data_str == '[DONE]':
                            break
                        
                        try:
                            chunk_data = json.loads(data_str)
                            delta = chunk_data.get('choices', [{}])[0].get('delta', {})
                            content = delta.get('content', '')
                            
                            if content:
                                full_response += content
                                yield content.encode('utf-8')
                        
                        except json.JSONDecodeError:
                            logger.warning(f'JSON 解析失败: {data_str[:100]}')
                            continue
                
                # 保存 AI 响应
                chat_sessions[persona].append({
                    'role': 'assistant',
                    'content': full_response,
                    'timestamp': datetime.now().isoformat(),
                })
                
                # 保存到数据库
                db.add_chat_message(persona, 'assistant', full_response, selected_model)
                
                # 生成记忆摘要
                if len(chat_sessions[persona]) >= 2:
                    last_conversation = chat_sessions[persona][-2:]
                    summary = generate_memory_summary(persona, last_conversation)
                    
                    if summary:
                        # 判断是否为公共记忆
                        is_public = any(keyword in summary for keyword in ['通用', '公共', '一般', '普遍'])
                        memory_manager.add_memory(persona, summary, is_public=is_public)
                        logger.info(f'记忆已保存: {summary[:50]}...')
            
            except Exception as e:
                logger.error(f'流式响应生成失败: {e}')
                yield f'错误: {str(e)}'.encode('utf-8')
        
        return Response(generate(), content_type='text/plain; charset=utf-8')
    
    except Exception as error:
        logger.error(f'聊天处理失败: {error}')
        return jsonify({'error': str(error)}), 500


# ==================== 记忆管理 API ====================

# 获取记忆列表
@app.route('/memories/<int:persona_id>', methods=['GET'])
def get_memories(persona_id):
    """获取指定 Persona 的所有记忆"""
    memories = memory_manager.get_all_memories(persona_id)
    return jsonify(memories)


# 获取实时记忆（支持搜索）
@app.route('/memories-live/<int:persona_id>', methods=['GET'])
def get_memories_live(persona_id):
    """获取实时记忆，支持搜索"""
    query = request.args.get('query', '')
    
    if query:
        # 使用语义检索
        memories = memory_manager.retrieve_memories(persona_id, query, limit=20)
    else:
        # 获取所有记忆
        memories = memory_manager.get_all_memories(persona_id)
    
    return jsonify(memories)


# 添加记忆
@app.route('/memories', methods=['POST'])
def add_memory():
    """手动添加记忆"""
    data = request.get_json()
    persona_id = data.get('personaId')
    content = data.get('content')
    is_public = data.get('isPublic', False)
    
    if not persona_id or not content:
        return jsonify({'error': '缺少必要参数'}), 400
    
    memory = memory_manager.add_memory(persona_id, content, is_public=is_public)
    return jsonify(memory)


# 更新记忆
@app.route('/memories/<int:memory_id>', methods=['PUT'])
def update_memory(memory_id):
    """更新记忆内容"""
    data = request.get_json()
    content = data.get('content')
    
    if not content:
        return jsonify({'error': '缺少内容'}), 400
    
    success = memory_manager.update_memory(memory_id, content=content)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': '更新失败'}), 500


# 删除记忆
@app.route('/memories/<int:memory_id>', methods=['DELETE'])
def delete_memory(memory_id):
    """删除记忆"""
    success = memory_manager.delete_memory(memory_id)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': '删除失败'}), 500


# 导出数据
@app.route('/export', methods=['GET'])
def export_data():
    """导出所有数据"""
    data = memory_manager.export_memories()
    
    response = Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        mimetype='application/json',
        headers={
            'Content-Disposition': f'attachment; filename=memories-{datetime.now().strftime("%Y%m%d")}.json'
        }
    )
    return response


# ==================== 启动服务器 ====================

if __name__ == '__main__':
    logger.info(f'🚀 服务器启动于 http://localhost:{PORT}')
    
    if not os.getenv('LONGCAT_API_KEY'):
        logger.warning('⚠️  LONGCAT_API_KEY 未设置，API 调用将失败')
    
    app.run(host='0.0.0.0', port=PORT, debug=False)
