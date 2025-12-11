#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
from src.utils.memory_manager import MemoryManager

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
CORS(app)

PORT = 3001

# 初始化记忆管理器
memory_manager = MemoryManager()

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
personas = [
    {'id': 1, 'name': '学术助手', 'description': '帮助进行学术研究和写作'},
    {'id': 2, 'name': '创意写作', 'description': '协助创意写作和故事创作'},
    {'id': 3, 'name': '技术支持', 'description': '提供技术问题解答'},
    {'id': 4, 'name': '翻译助手', 'description': '多语言翻译服务'},
]

chat_sessions = {}  # 存储每个 persona 的聊天记录
current_models = {}  # 存储每个 persona 当前使用的模型


# 获取 Persona 列表
@app.route('/personas', methods=['GET'])
def get_personas():
    return jsonify(personas)


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
        persona_obj = next((p for p in personas if p['id'] == persona_id), None)
        
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
    
    # 验证 persona ID
    if not any(p['id'] == persona for p in personas):
        return jsonify({'error': '无效的 Persona ID'}), 400
    
    # 验证消息长度
    if len(message) > 5000:
        return jsonify({'error': '消息过长，最多 5000 字符'}), 400
    
    try:
        # 验证并选择模型
        valid_models = [DEFAULT_MODEL, THINKING_MODEL]
        selected_model = model or current_models.get(persona, DEFAULT_MODEL)
        if selected_model not in valid_models:
            selected_model = DEFAULT_MODEL
        
        persona_obj = next((p for p in personas if p['id'] == persona), None)
        
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
        
        # 调用 LongCat API
        logger.info(f'[Chat] 调用 API - Persona: {persona}, Model: {selected_model}')
        api_response = call_longcat_api(selected_model, messages, stream=True)
        
        logger.info(f'[Chat] API 响应状态: {api_response.status_code}')
        logger.info(f'[Chat] 响应 Content-Type: {api_response.headers.get("content-type", "")}, Content-Length: {api_response.headers.get("content-length", "unknown")}')
        
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
                            continue
                        
                        try:
                            chunk_data = json.loads(data_str)
                            content = chunk_data.get('choices', [{}])[0].get('delta', {}).get('content', '') or \
                                     chunk_data.get('choices', [{}])[0].get('message', {}).get('content', '')
                            if content:
                                full_response += content
                                yield content
                                if len(full_response) % 50 == 0:
                                    logger.info(f'[Chat] 已发送 {len(full_response)} 字符')
                        except json.JSONDecodeError as e:
                            logger.warning(f'解析 SSE 数据失败: {e}, line: {line}')
                    else:
                        # 如果不是 SSE 格式，尝试直接解析 JSON
                        try:
                            chunk_data = json.loads(line)
                            content = chunk_data.get('choices', [{}])[0].get('delta', {}).get('content', '') or \
                                     chunk_data.get('choices', [{}])[0].get('message', {}).get('content', '')
                            if content:
                                full_response += content
                                yield content
                        except json.JSONDecodeError:
                            pass
                
                logger.info(f'[Chat] 流式响应完成，总长度: {len(full_response)} 字符')

                # 如果流式返回为空，尝试非流式回退（某些后端在 stream 模式下可能不会返回 SSE 内容）
                if not full_response.strip():
                    logger.warning('[Chat] 警告：流式响应内容为空，尝试非流式回退...')
                    try:
                        nonstream_resp = call_longcat_api(selected_model, messages, stream=False)
                        try:
                            data = nonstream_resp.json()
                        except Exception as e:
                            logger.error(f'[Chat] 非流式回退解析 JSON 失败: {e}')
                            data = {}

                        # 尝试兼容不同返回格式（choices[].message.content 或 choices[].text）
                        content = ''
                        try:
                            content = data.get('choices', [{}])[0].get('message', {}).get('content', '') or \
                                      data.get('choices', [{}])[0].get('text', '')
                        except Exception:
                            content = ''

                        if content:
                            full_response = content
                            # 立即把回退内容发送给客户端
                            yield content
                        else:
                            logger.warning('[Chat] 非流式回退也未返回内容')
                    except Exception as e:
                        logger.error(f'[Chat] 非流式回退调用失败: {e}')
                
                # 统一保存 AI 响应（无论是流式还是非流式）
                if full_response.strip():
                    chat_sessions[persona].append({
                        'role': 'assistant',
                        'content': full_response,
                        'timestamp': datetime.now().isoformat(),
                    })
                
                # 更新记忆权重（访问相关记忆）
                for memory in relevant_memories:
                    memory_manager.update_memory_weight(memory['id'], persona, 0.1)  # 增加增量
                
                # 在后台生成记忆摘要（异步）
                def save_memory_async():
                    try:
                        time.sleep(0.5)
                        session = chat_sessions.get(persona, [])
                        if len(session) >= 2:
                            last_two_messages = session[-2:]
                            if last_two_messages[0]['role'] == 'user' and last_two_messages[1]['role'] == 'assistant':
                                summary = generate_memory_summary(persona, last_two_messages)
                                if summary and summary.strip():
                                    is_public = any(keyword in summary for keyword in ['通用', '公共', '一般', '共同'])
                                    memory_manager.add_memory(persona, summary.strip(), is_public)
                                    logger.info(f'✅ 记忆已保存 (Persona {persona}, {"公共" if is_public else "角色"}): {summary.strip()}')
                    except Exception as e:
                        logger.error(f'❌ 保存记忆失败: {e}')
                
                memory_thread = Thread(target=save_memory_async, daemon=True)
                memory_thread.start()
                
                # 定期合并相似记忆（每10轮对话）
                if len(chat_sessions.get(persona, [])) % 10 == 0:
                    memory_manager.merge_similar_memories(persona)
                
            except Exception as stream_error:
                logger.error(f'流式读取错误: {stream_error}')
        
        return Response(generate(), mimetype='text/plain; charset=utf-8')
    
    except Exception as error:
        logger.error(f'聊天错误: {error}')
        return jsonify({'error': str(error)}), 500


# 获取记忆
@app.route('/memories/<int:persona_id>', methods=['GET'])
def get_memories(persona_id):
    memories = memory_manager.get_all_memories(persona_id)
    return jsonify(memories)


# 获取实时记忆（用于前端显示）
@app.route('/memories-live/<int:persona_id>', methods=['GET'])
def get_memories_live(persona_id):
    query = request.args.get('query', '')
    
    if query:
        relevant_memories = memory_manager.retrieve_memories(persona_id, query, 10)
        return jsonify(relevant_memories)
    else:
        memories = memory_manager.get_all_memories(persona_id)
        all_memories = []
        
        for m in memories.get('persona', []):
            m_copy = m.copy()
            m_copy['type'] = 'persona'
            all_memories.append(m_copy)
        
        for m in memories.get('public', []):
            m_copy = m.copy()
            m_copy['type'] = 'public'
            all_memories.append(m_copy)
        
        # 按时间戳排序
        all_memories.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return jsonify(all_memories[:20])


# 手动添加记忆
@app.route('/memories', methods=['POST'])
def add_memory():
    data = request.get_json()
    persona_id = data.get('personaId')
    content = data.get('content')
    is_public = data.get('isPublic', False)
    
    if not persona_id or not content:
        return jsonify({'error': '缺少必要参数'}), 400
    
    memory = memory_manager.add_memory(persona_id, content, is_public)
    return jsonify({'success': True, 'memory': memory})


# 导出数据
@app.route('/export', methods=['GET'])
def export_data():
    export_data = {
        'personas': personas,
        'chatSessions': chat_sessions,
        'memories': {str(k): v for k, v in memory_manager.memories.items()},
        'publicMemories': memory_manager.public_memories,
        'exportDate': datetime.now().isoformat(),
    }
    
    response = jsonify(export_data)
    response.headers['Content-Disposition'] = 'attachment; filename=annotations.json'
    return response


if __name__ == '__main__':
    logger.info(f'服务器运行在 http://localhost:{PORT}')
    logger.info(f'LongCat API: {LONGCAT_API_BASE}')
    
    # 检查 API Key 是否设置
    if not os.getenv('LONGCAT_API_KEY'):
        logger.warning('\n⚠️  警告：LONGCAT_API_KEY 未设置！')
        logger.warning('请创建 .env 文件并添加：')
        logger.warning('LONGCAT_API_KEY=your_api_key_here\n')
        logger.warning('或者设置环境变量：')
        logger.warning('export LONGCAT_API_KEY=your_api_key_here  (Linux/Mac)')
        logger.warning('set LONGCAT_API_KEY=your_api_key_here     (Windows)\n')
    else:
        logger.info('✅ API Key 已设置')
    
    # 根据环境选择绑定地址
    host = '0.0.0.0' if os.getenv('ENV') == 'production' else 'localhost'
    app.run(host=host, port=PORT, debug=False)
