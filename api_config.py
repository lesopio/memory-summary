#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API 配置管理模块
支持多种 AI 服务提供商的统一接口
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class APIConfig:
    """API 配置类"""
    
    # 支持的 API 提供商
    PROVIDERS = {
        'longcat': {
            'name': 'LongCat',
            'base_url': 'https://api.longcat.chat/openai',
            'api_key_env': 'LONGCAT_API_KEY',
            'models': ['LongCat-Flash-Chat', 'LongCat-Flash-Thinking'],
            'supports_stream': True,
        },
        'openai': {
            'name': 'OpenAI',
            'base_url': 'https://api.openai.com',
            'api_key_env': 'OPENAI_API_KEY',
            'models': ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'],
            'supports_stream': True,
        },
        'anthropic': {
            'name': 'Anthropic Claude',
            'base_url': 'https://api.anthropic.com',
            'api_key_env': 'ANTHROPIC_API_KEY',
            'models': ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'],
            'supports_stream': True,
        },
        'ollama': {
            'name': 'Ollama (本地)',
            'base_url': 'http://localhost:11434',
            'api_key_env': None,  # Ollama 不需要 API Key
            'models': ['llama2', 'mistral', 'codellama'],
            'supports_stream': True,
        },
        'custom': {
            'name': '自定义 OpenAI 兼容 API',
            'base_url': os.getenv('CUSTOM_API_BASE_URL', 'http://localhost:8000'),
            'api_key_env': 'CUSTOM_API_KEY',
            'models': [],  # 由用户自定义
            'supports_stream': True,
        },
    }
    
    def __init__(self, provider: str = 'longcat'):
        """
        初始化 API 配置
        
        Args:
            provider: API 提供商名称
        """
        self.provider = provider
        self.config = self.PROVIDERS.get(provider, self.PROVIDERS['longcat'])
        self.api_key = self._get_api_key()
        self.base_url = self.config['base_url']
        self.models = self.config['models']
        self.supports_stream = self.config['supports_stream']
    
    def _get_api_key(self) -> Optional[str]:
        """获取 API Key"""
        key_env = self.config.get('api_key_env')
        if key_env:
            return os.getenv(key_env, '')
        return None
    
    def is_configured(self) -> bool:
        """检查 API 是否已配置"""
        if self.config.get('api_key_env'):
            return bool(self.api_key)
        return True  # 不需要 API Key 的服务（如 Ollama）
    
    def get_endpoint(self, endpoint_type: str = 'chat') -> str:
        """
        获取 API 端点 URL
        
        Args:
            endpoint_type: 端点类型 ('chat', 'completion', 'embedding')
        """
        if self.provider == 'anthropic':
            return f'{self.base_url}/v1/messages'
        elif self.provider == 'ollama':
            return f'{self.base_url}/api/chat'
        else:
            # OpenAI 兼容格式
            return f'{self.base_url}/v1/chat/completions'
    
    def get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            'Content-Type': 'application/json',
        }
        
        if self.api_key:
            if self.provider == 'anthropic':
                headers['x-api-key'] = self.api_key
                headers['anthropic-version'] = '2023-06-01'
            else:
                headers['Authorization'] = f'Bearer {self.api_key}'
        
        return headers
    
    def format_messages(self, messages: List[Dict]) -> Any:
        """
        格式化消息为特定 API 格式
        
        Args:
            messages: 标准消息列表
        
        Returns:
            格式化后的消息
        """
        if self.provider == 'anthropic':
            # Anthropic 使用不同的消息格式
            system_message = None
            formatted_messages = []
            
            for msg in messages:
                if msg['role'] == 'system':
                    system_message = msg['content']
                else:
                    formatted_messages.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
            
            return {
                'system': system_message,
                'messages': formatted_messages
            }
        else:
            # OpenAI 兼容格式
            return messages
    
    def build_request_body(self, model: str, messages: List[Dict], 
                          temperature: float = 0.7, stream: bool = True) -> Dict:
        """
        构建请求体
        
        Args:
            model: 模型名称
            messages: 消息列表
            temperature: 温度参数
            stream: 是否流式输出
        """
        if self.provider == 'anthropic':
            formatted = self.format_messages(messages)
            body = {
                'model': model,
                'messages': formatted['messages'],
                'max_tokens': 4096,
                'temperature': temperature,
                'stream': stream,
            }
            if formatted['system']:
                body['system'] = formatted['system']
            return body
        else:
            # OpenAI 兼容格式
            return {
                'model': model,
                'messages': messages,
                'temperature': temperature,
                'stream': stream,
            }
    
    def parse_stream_response(self, line: str) -> Optional[str]:
        """
        解析流式响应
        
        Args:
            line: 响应行
        
        Returns:
            提取的内容文本
        """
        if not line.strip():
            return None
        
        # 处理 SSE 格式
        if line.startswith('data: '):
            data_str = line[6:].strip()
            
            if data_str == '[DONE]':
                return None
            
            try:
                chunk_data = json.loads(data_str)
                
                if self.provider == 'anthropic':
                    # Anthropic 格式
                    if chunk_data.get('type') == 'content_block_delta':
                        delta = chunk_data.get('delta', {})
                        return delta.get('text', '')
                else:
                    # OpenAI 兼容格式
                    delta = chunk_data.get('choices', [{}])[0].get('delta', {})
                    return delta.get('content', '')
            
            except json.JSONDecodeError:
                logger.warning(f'JSON 解析失败: {data_str[:100]}')
                return None
        
        return None
    
    @classmethod
    def get_available_providers(cls) -> List[Dict]:
        """获取所有可用的 API 提供商"""
        providers = []
        for key, config in cls.PROVIDERS.items():
            api_key_env = config.get('api_key_env')
            is_configured = not api_key_env or bool(os.getenv(api_key_env))
            
            providers.append({
                'id': key,
                'name': config['name'],
                'models': config['models'],
                'configured': is_configured,
            })
        
        return providers
    
    @classmethod
    def get_all_models(cls) -> List[Dict]:
        """获取所有可用的模型"""
        models = []
        for provider_key, config in cls.PROVIDERS.items():
            api_key_env = config.get('api_key_env')
            is_configured = not api_key_env or bool(os.getenv(api_key_env))
            
            if is_configured:
                for model in config['models']:
                    models.append({
                        'id': f'{provider_key}:{model}',
                        'name': model,
                        'provider': config['name'],
                        'provider_id': provider_key,
                    })
        
        return models


def get_api_config(provider: str = None, model: str = None) -> APIConfig:
    """
    获取 API 配置实例
    
    Args:
        provider: 提供商 ID
        model: 模型名称（格式: provider:model）
    
    Returns:
        APIConfig 实例
    """
    if model and ':' in model:
        provider, _ = model.split(':', 1)
    
    if not provider:
        # 默认使用 LongCat
        provider = 'longcat'
    
    return APIConfig(provider)


if __name__ == '__main__':
    # 测试 API 配置
    logging.basicConfig(level=logging.INFO)
    
    # 获取所有可用提供商
    providers = APIConfig.get_available_providers()
    print('可用的 API 提供商:')
    for p in providers:
        status = '✅ 已配置' if p['configured'] else '❌ 未配置'
        print(f'  - {p["name"]} ({p["id"]}): {status}')
        print(f'    模型: {", ".join(p["models"])}')
    
    # 获取所有可用模型
    models = APIConfig.get_all_models()
    print(f'\n可用的模型总数: {len(models)}')
    for m in models[:5]:  # 只显示前5个
        print(f'  - {m["name"]} ({m["provider"]})')
    
    # 测试 LongCat 配置
    print('\n测试 LongCat 配置:')
    config = APIConfig('longcat')
    print(f'  - 端点: {config.get_endpoint()}')
    print(f'  - 已配置: {config.is_configured()}')
    print(f'  - 支持流式: {config.supports_stream}')
