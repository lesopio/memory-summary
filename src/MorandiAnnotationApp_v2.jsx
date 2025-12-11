import React, { useState, useEffect, useRef } from 'react';
import { Button } from './components/ui/button';
import { Card, CardContent } from './components/ui/card';
import { Input } from './components/ui/input';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Brain, Zap, Download, RefreshCw, Menu, X, Search, Edit2, Trash2, Filter } from 'lucide-react';

const DEFAULT_MODEL = 'LongCat-Flash-Chat';
const THINKING_MODEL = 'LongCat-Flash-Thinking';

export default function MorandiAnnotationApp() {
  const [personas, setPersonas] = useState([]);
  const [currentPersona, setCurrentPersona] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [memories, setMemories] = useState([]);
  const [currentModel, setCurrentModel] = useState(DEFAULT_MODEL);
  const [memoryLoading, setMemoryLoading] = useState(false);
  
  // 移动端状态
  const [showPersonaPanel, setShowPersonaPanel] = useState(false);
  const [showMemoryPanel, setShowMemoryPanel] = useState(false);
  
  // 记忆搜索和筛选
  const [memorySearchQuery, setMemorySearchQuery] = useState('');
  const [memoryFilter, setMemoryFilter] = useState('all'); // 'all', 'public', 'private'
  const [editingMemory, setEditingMemory] = useState(null);
  
  const messagesEndRef = useRef(null);
  const memoryEndRef = useRef(null);

  const loadPersonas = async () => {
    try {
      setError(null);
      const res = await fetch('/personas');
      if (!res.ok) throw new Error('加载 Persona 列表失败');
      const data = await res.json();
      setPersonas(data);
      if (data.length > 0) {
        setCurrentPersona(data[0]);
        loadChatHistory(data[0].id);
        loadMemories(data[0].id);
      }
    } catch (err) {
      setError(err.message);
      console.error('加载 Persona 失败:', err);
    }
  };

  const loadChatHistory = (personaId) => {
    // 这里可以从后端加载历史记录，暂时使用空数组
    setChatHistory([]);
  };

  const loadMemories = async (personaId, query = '') => {
    try {
      setMemoryLoading(true);
      const url = query
        ? `/memories-live/${personaId}?query=${encodeURIComponent(query)}`
        : `/memories-live/${personaId}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('加载记忆失败');
      const data = await res.json();
      setMemories(data);
    } catch (err) {
      console.error('加载记忆失败:', err);
    } finally {
      setMemoryLoading(false);
    }
  };

  const switchModel = async (model) => {
    if (!currentPersona) return;
    try {
      const res = await fetch('/switch-model', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ persona: currentPersona.id, model }),
      });
      if (res.ok) {
        setCurrentModel(model);
      }
    } catch (err) {
      console.error('切换模型失败:', err);
    }
  };

  const sendMessage = async () => {
    if (!message.trim() || !currentPersona || loading) return;

    try {
      setLoading(true);
      setError(null);
      const userMessage = message.trim();
      setChatHistory(prev => [...prev, { role: 'user', content: userMessage }]);
      setMessage('');

      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          persona: currentPersona.id,
          message: userMessage,
          model: currentModel,
        }),
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`发送消息失败: ${res.status} - ${errorText}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let aiResponse = '';
      let hasContent = false;
      let chunkCount = 0;

      // 先添加一个临时 assistant 消息
      setChatHistory(prev => [...prev, { role: 'assistant-temp', content: '' }]);

      try {
        while (true) {
          const { value, done } = await reader.read();
          if (done) {
            console.log('[Frontend] 流式读取完成，共接收', chunkCount, '个数据块');
            break;
          }
          
          if (value) {
            chunkCount++;
            const chunk = decoder.decode(value, { stream: true });
            if (chunk) {
              hasContent = true;
              aiResponse += chunk;
              
              // 立即更新 UI
              setChatHistory((prev) => {
                const newHistory = prev.map((msg, index) => {
                  if (index === prev.length - 1 && msg.role === 'assistant-temp') {
                    return { ...msg, content: aiResponse };
                  }
                  return msg;
                });
                return newHistory;
              });
            }
          }
        }

        if (!hasContent && !aiResponse.trim()) {
          console.warn('[Frontend] 未接收到响应内容');
          setChatHistory(prev => {
            const newHistory = prev.map((msg, index) => {
              if (index === prev.length - 1 && msg.role === 'assistant-temp') {
                return {
                  ...msg,
                  content: '抱歉，未收到响应。请检查 API 配置或重试。'
                };
              }
              return msg;
            });
            return newHistory;
          });
        }
      } catch (streamError) {
        console.error('读取流式响应失败:', streamError);
        setChatHistory(prev => {
          const updated = [...prev];
          const lastIndex = updated.length - 1;
          if (lastIndex >= 0 && updated[lastIndex]?.role === 'assistant-temp') {
            updated[lastIndex] = {
              ...updated[lastIndex],
              content: `错误: ${streamError.message || '读取响应失败'}`
            };
          }
          return updated;
        });
      }

      // 将临时消息标记为正式的 assistant 消息
      setChatHistory((prev) => {
        const updated = [...prev];
        if (updated.length > 0 && updated[updated.length - 1]?.role === 'assistant-temp') {
          updated[updated.length - 1] = { ...updated[updated.length - 1], role: 'assistant' };
        }
        return updated;
      });

      // 对话结束后刷新记忆
      setTimeout(() => {
        loadMemories(currentPersona.id);
      }, 1500);
    } catch (err) {
      setError(err.message);
      console.error('发送消息失败:', err);
      setChatHistory(prev => prev.slice(0, -1));
    } finally {
      setLoading(false);
    }
  };

  const deleteMemory = async (memoryId) => {
    if (!confirm('确定要删除这条记忆吗？')) return;
    
    try {
      const res = await fetch(`/memories/${memoryId}`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error('删除记忆失败');
      
      // 刷新记忆列表
      loadMemories(currentPersona.id);
    } catch (err) {
      console.error('删除记忆失败:', err);
      alert('删除失败: ' + err.message);
    }
  };

  const updateMemory = async (memoryId, newContent) => {
    try {
      const res = await fetch(`/memories/${memoryId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: newContent }),
      });
      if (!res.ok) throw new Error('更新记忆失败');
      
      setEditingMemory(null);
      loadMemories(currentPersona.id);
    } catch (err) {
      console.error('更新记忆失败:', err);
      alert('更新失败: ' + err.message);
    }
  };

  useEffect(() => {
    loadPersonas();
  }, []);

  useEffect(() => {
    if (currentPersona) {
      loadChatHistory(currentPersona.id);
      loadMemories(currentPersona.id);
      setCurrentModel(DEFAULT_MODEL);
    }
  }, [currentPersona]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  useEffect(() => {
    memoryEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [memories]);

  // 定期刷新记忆
  useEffect(() => {
    if (!currentPersona) return;
    const interval = setInterval(() => {
      loadMemories(currentPersona.id);
    }, 5000);

    return () => clearInterval(interval);
  }, [currentPersona]);

  const exportData = async () => {
    try {
      setError(null);
      const res = await fetch('/export');
      if (!res.ok) throw new Error('导出失败');

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `memories-${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message);
      console.error('导出失败:', err);
      alert('导出失败: ' + err.message);
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // 筛选记忆
  const filteredMemories = memories.filter(memory => {
    // 类型筛选
    if (memoryFilter === 'public' && memory.type !== 'public') return false;
    if (memoryFilter === 'private' && memory.type === 'public') return false;
    
    // 搜索筛选
    if (memorySearchQuery && !memory.content.toLowerCase().includes(memorySearchQuery.toLowerCase())) {
      return false;
    }
    
    return true;
  });

  return (
    <div className="flex flex-col lg:grid lg:grid-cols-4 h-screen bg-haze-blue-50 text-haze-blue-900">
      {error && (
        <div className="fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg z-50">
          {error}
        </div>
      )}

      {/* 移动端顶部导航栏 */}
      <div className="lg:hidden bg-morandi-green-600 text-white p-4 flex items-center justify-between">
        <button
          onClick={() => setShowPersonaPanel(!showPersonaPanel)}
          className="p-2 hover:bg-morandi-green-700 rounded"
        >
          <Menu className="w-6 h-6" />
        </button>
        <h1 className="text-lg font-semibold">
          {currentPersona ? currentPersona.name : '选择 Persona'}
        </h1>
        <button
          onClick={() => setShowMemoryPanel(!showMemoryPanel)}
          className="p-2 hover:bg-morandi-green-700 rounded"
        >
          <Brain className="w-6 h-6" />
        </button>
      </div>

      {/* 左侧 Persona 列表 - 响应式 */}
      <AnimatePresence>
        {(showPersonaPanel || window.innerWidth >= 1024) && (
          <motion.div
            initial={{ x: -300 }}
            animate={{ x: 0 }}
            exit={{ x: -300 }}
            className="fixed lg:relative lg:col-span-1 inset-y-0 left-0 w-80 lg:w-auto bg-morandi-green-100 p-4 overflow-y-auto border-r border-morandi-green-200 z-40"
          >
            <div className="flex items-center justify-between mb-4 lg:hidden">
              <h2 className="text-lg font-semibold text-morandi-green-800">Persona 列表</h2>
              <button
                onClick={() => setShowPersonaPanel(false)}
                className="p-1 hover:bg-morandi-green-200 rounded"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <h2 className="hidden lg:block text-lg font-semibold mb-4 text-morandi-green-800">Persona 列表</h2>
            
            {personas.length === 0 ? (
              <div className="text-center text-haze-blue-600 mt-4">
                {error ? '加载失败' : '加载中...'}
              </div>
            ) : (
              personas.map((p) => (
                <motion.div
                  key={p.id}
                  whileHover={{ scale: 1.02 }}
                  onClick={() => {
                    setCurrentPersona(p);
                    setShowPersonaPanel(false);
                  }}
                  className={`cursor-pointer rounded-xl p-3 mb-2 transition-colors ${
                    currentPersona?.id === p.id
                      ? 'bg-haze-blue-600 text-white shadow-md'
                      : 'bg-morandi-green-50 text-morandi-green-700 hover:bg-morandi-green-200'
                  }`}
                >
                  {p.name}
                </motion.div>
              ))
            )}

            {/* 模型切换 */}
            {currentPersona && (
              <div className="mt-6 pt-6 border-t border-morandi-green-200">
                <h3 className="text-sm font-semibold mb-3 text-morandi-green-800">模型选择</h3>
                <div className="space-y-2">
                  <button
                    onClick={() => switchModel(DEFAULT_MODEL)}
                    className={`w-full rounded-lg p-2 text-sm transition-colors flex items-center gap-2 ${
                      currentModel === DEFAULT_MODEL
                        ? 'bg-haze-blue-600 text-white'
                        : 'bg-morandi-green-50 text-morandi-green-700 hover:bg-morandi-green-200'
                    }`}
                  >
                    <Zap className="w-4 h-4" />
                    Flash-Chat
                  </button>
                  <button
                    onClick={() => switchModel(THINKING_MODEL)}
                    className={`w-full rounded-lg p-2 text-sm transition-colors flex items-center gap-2 ${
                      currentModel === THINKING_MODEL
                        ? 'bg-haze-blue-600 text-white'
                        : 'bg-morandi-green-50 text-morandi-green-700 hover:bg-morandi-green-200'
                    }`}
                  >
                    <Brain className="w-4 h-4" />
                    Flash-Thinking
                  </button>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* 中间聊天区域 - 响应式 */}
      <div className="flex-1 lg:col-span-2 flex flex-col bg-haze-blue-50 border-x border-haze-blue-200">
        {!currentPersona ? (
          <div className="flex-1 flex items-center justify-center text-haze-blue-500">
            请选择一个 Persona 开始对话
          </div>
        ) : (
          <>
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {chatHistory.length === 0 ? (
                <div className="flex items-center justify-center h-full text-haze-blue-500">
                  开始与 {currentPersona.name} 对话吧
                </div>
              ) : (
                chatHistory.map((msg, i) => (
                  <Card
                    key={i}
                    className={`max-w-[85%] md:max-w-[80%] ${
                      msg.role === 'user'
                        ? 'ml-auto bg-haze-blue-600 text-white'
                        : 'mr-auto bg-morandi-green-100 text-morandi-green-800'
                    }`}
                  >
                    <CardContent className="p-3 text-sm md:text-base">
                      {msg.content || '思考中...'}
                    </CardContent>
                  </Card>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>
            <div className="p-3 md:p-4 flex gap-2 border-t border-haze-blue-200 bg-white">
              <Input
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                placeholder="输入消息..."
                disabled={loading}
                className="flex-1 bg-haze-blue-50 border-haze-blue-200 focus:ring-haze-blue-500 text-sm md:text-base"
              />
              <Button
                onClick={sendMessage}
                disabled={loading || !message.trim()}
                className="bg-haze-blue-600 hover:bg-haze-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed px-3 md:px-4"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </>
        )}
      </div>

      {/* 右侧记忆显示区域 - 响应式 */}
      <AnimatePresence>
        {(showMemoryPanel || window.innerWidth >= 1024) && (
          <motion.div
            initial={{ x: 300 }}
            animate={{ x: 0 }}
            exit={{ x: 300 }}
            className="fixed lg:relative lg:col-span-1 inset-y-0 right-0 w-80 lg:w-auto bg-morandi-green-50 p-4 flex flex-col border-l border-morandi-green-200 z-40"
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-morandi-green-800 flex items-center gap-2">
                <Brain className="w-5 h-5" />
                记忆库
              </h2>
              <div className="flex gap-1">
                <button
                  onClick={() => loadMemories(currentPersona?.id)}
                  className="p-1 hover:bg-morandi-green-200 rounded transition-colors"
                  title="刷新记忆"
                >
                  <RefreshCw className={`w-4 h-4 text-morandi-green-700 ${memoryLoading ? 'animate-spin' : ''}`} />
                </button>
                <button
                  onClick={() => setShowMemoryPanel(false)}
                  className="p-1 hover:bg-morandi-green-200 rounded lg:hidden"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* 搜索和筛选 */}
            <div className="mb-3 space-y-2">
              <div className="relative">
                <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-haze-blue-400" />
                <Input
                  value={memorySearchQuery}
                  onChange={(e) => setMemorySearchQuery(e.target.value)}
                  placeholder="搜索记忆..."
                  className="pl-8 text-sm bg-white border-morandi-green-200"
                />
              </div>
              <div className="flex gap-1">
                <button
                  onClick={() => setMemoryFilter('all')}
                  className={`flex-1 px-2 py-1 text-xs rounded ${
                    memoryFilter === 'all'
                      ? 'bg-haze-blue-600 text-white'
                      : 'bg-morandi-green-100 text-morandi-green-700 hover:bg-morandi-green-200'
                  }`}
                >
                  全部
                </button>
                <button
                  onClick={() => setMemoryFilter('public')}
                  className={`flex-1 px-2 py-1 text-xs rounded ${
                    memoryFilter === 'public'
                      ? 'bg-haze-blue-600 text-white'
                      : 'bg-morandi-green-100 text-morandi-green-700 hover:bg-morandi-green-200'
                  }`}
                >
                  公共
                </button>
                <button
                  onClick={() => setMemoryFilter('private')}
                  className={`flex-1 px-2 py-1 text-xs rounded ${
                    memoryFilter === 'private'
                      ? 'bg-haze-blue-600 text-white'
                      : 'bg-morandi-green-100 text-morandi-green-700 hover:bg-morandi-green-200'
                  }`}
                >
                  私有
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2">
              {!currentPersona ? (
                <div className="text-center text-haze-blue-500 mt-8">请先选择 Persona</div>
              ) : filteredMemories.length === 0 ? (
                <div className="text-center text-haze-blue-500 mt-8">
                  {memoryLoading ? '加载中...' : '暂无记忆'}
                </div>
              ) : (
                filteredMemories.map((memory) => (
                  <motion.div
                    key={memory.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`p-3 rounded-lg text-sm ${
                      memory.type === 'public'
                        ? 'bg-haze-blue-100 border border-haze-blue-300'
                        : 'bg-morandi-green-100 border border-morandi-green-300'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-1">
                      <span
                        className={`text-xs px-2 py-0.5 rounded ${
                          memory.type === 'public'
                            ? 'bg-haze-blue-200 text-haze-blue-700'
                            : 'bg-morandi-green-200 text-morandi-green-700'
                        }`}
                      >
                        {memory.type === 'public' ? '公共记忆' : '角色记忆'}
                      </span>
                      <div className="flex gap-1">
                        <button
                          onClick={() => setEditingMemory(memory)}
                          className="p-1 hover:bg-haze-blue-200 rounded"
                          title="编辑"
                        >
                          <Edit2 className="w-3 h-3 text-haze-blue-600" />
                        </button>
                        <button
                          onClick={() => deleteMemory(memory.id)}
                          className="p-1 hover:bg-red-200 rounded"
                          title="删除"
                        >
                          <Trash2 className="w-3 h-3 text-red-600" />
                        </button>
                      </div>
                    </div>
                    
                    {editingMemory?.id === memory.id ? (
                      <div className="space-y-2">
                        <textarea
                          defaultValue={memory.content}
                          className="w-full p-2 text-sm border border-haze-blue-300 rounded resize-none"
                          rows={3}
                          id={`edit-${memory.id}`}
                        />
                        <div className="flex gap-2">
                          <button
                            onClick={() => {
                              const newContent = document.getElementById(`edit-${memory.id}`).value;
                              updateMemory(memory.id, newContent);
                            }}
                            className="flex-1 px-2 py-1 text-xs bg-haze-blue-600 text-white rounded hover:bg-haze-blue-700"
                          >
                            保存
                          </button>
                          <button
                            onClick={() => setEditingMemory(null)}
                            className="flex-1 px-2 py-1 text-xs bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
                          >
                            取消
                          </button>
                        </div>
                      </div>
                    ) : (
                      <>
                        <p className="text-haze-blue-800 leading-relaxed mb-1">{memory.content}</p>
                        <div className="flex items-center justify-between text-xs text-haze-blue-600">
                          <span>{formatTime(memory.timestamp)}</span>
                          {memory.score && (
                            <span>相关度: {(memory.score * 100).toFixed(1)}%</span>
                          )}
                        </div>
                      </>
                    )}
                  </motion.div>
                ))
              )}
              <div ref={memoryEndRef} />
            </div>

            <div className="mt-4 pt-4 border-t border-morandi-green-200">
              <Button
                onClick={exportData}
                className="w-full bg-haze-blue-600 hover:bg-haze-blue-700 text-white text-sm"
              >
                <Download className="w-4 h-4 mr-2" /> 导出记忆
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 移动端遮罩层 */}
      {(showPersonaPanel || showMemoryPanel) && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-30 lg:hidden"
          onClick={() => {
            setShowPersonaPanel(false);
            setShowMemoryPanel(false);
          }}
        />
      )}
    </div>
  );
}
