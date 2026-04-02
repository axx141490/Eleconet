import { useState, useEffect, useRef } from 'react';
import { useSearchParams, useParams } from 'react-router-dom';
import { chatAPI, kbAPI } from '../services/api';
import { Send, Bot, User, Database, Loader } from 'lucide-react';
import toast from 'react-hot-toast';

export default function ChatPage() {
  const [searchParams] = useSearchParams();
  const { conversationId: paramConvId } = useParams();
  const [kbs, setKBs] = useState([]);
  const [selectedKB, setSelectedKB] = useState(searchParams.get('kb') || '');
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(paramConvId ? Number(paramConvId) : null);
  const messagesEndRef = useRef(null);

  useEffect(() => { loadKBs(); }, []);

  useEffect(() => {
    if (paramConvId) loadConversation(paramConvId);
  }, [paramConvId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadKBs = async () => {
    try {
      const res = await kbAPI.list();
      setKBs(res.data);
      // Auto-select if KB from URL
      const urlKB = searchParams.get('kb');
      if (urlKB) setSelectedKB(urlKB);
      else if (res.data.length > 0 && !selectedKB) setSelectedKB(String(res.data[0].id));
    } catch { /* ignore */ }
  };

  const loadConversation = async (id) => {
    try {
      const res = await chatAPI.getConversation(id);
      setMessages(res.data.messages.map((m) => ({
        role: m.role,
        content: m.content,
        sources: m.sources,
      })));
      setConversationId(Number(id));
      if (res.data.kb_id) setSelectedKB(String(res.data.kb_id));
    } catch { /* ignore */ }
  };

  const handleSend = async () => {
    if (!input.trim() || !selectedKB) {
      toast.error(!selectedKB ? '请先选择一个知识库' : '请输入问题');
      return;
    }
    const question = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: question }]);
    setLoading(true);

    try {
      const res = await chatAPI.send({
        question,
        kb_id: Number(selectedKB),
        conversation_id: conversationId,
        top_k: 5,
      });
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: res.data.answer,
        sources: res.data.sources,
      }]);
      setConversationId(res.data.conversation_id);
    } catch (err) {
      toast.error(err.response?.data?.detail || '问答失败');
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: '抱歉，处理你的问题时出错了。请确认知识库中已有相关文档。',
      }]);
    } finally { setLoading(false); }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const startNewChat = () => {
    setMessages([]);
    setConversationId(null);
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <Bot size={24} color="var(--primary)" />
        <h2 style={{ fontSize: 20, flex: 1 }}>智能问答</h2>
        <select
          value={selectedKB}
          onChange={(e) => { setSelectedKB(e.target.value); startNewChat(); }}
          style={{ width: 200, padding: '8px 12px', borderRadius: 8, border: '1px solid var(--border)' }}
        >
          <option value="">选择知识库</option>
          {kbs.map((kb) => (
            <option key={kb.id} value={kb.id}>{kb.name}</option>
          ))}
        </select>
        <button className="btn btn-secondary btn-sm" onClick={startNewChat}>新对话</button>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="empty-state">
            <Bot size={48} />
            <h3>开始提问吧！</h3>
            <p>选择一个知识库，然后输入你的问题</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <div className="message-avatar">
              {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
            </div>
            <div className="message-bubble">
              <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
              {msg.sources?.length > 0 && (
                <div className="message-sources">
                  <Database size={12} style={{ marginRight: 4 }} />
                  来源：
                  {msg.sources.map((s, j) => (
                    <span key={j}>{s.document} ({(s.relevance_score * 100).toFixed(0)}%)</span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="message assistant">
            <div className="message-avatar"><Bot size={16} /></div>
            <div className="message-bubble">
              <Loader size={16} className="spinner" style={{ display: 'inline-block', marginRight: 8 }} />
              正在思考中...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={selectedKB ? '输入你的问题...' : '请先选择知识库'}
          disabled={!selectedKB || loading}
        />
        <button
          className="btn btn-primary"
          onClick={handleSend}
          disabled={!input.trim() || !selectedKB || loading}
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}
