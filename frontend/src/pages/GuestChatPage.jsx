import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { guestAPI } from '../services/api';
import { Send, Bot, User, Loader } from 'lucide-react';
import toast from 'react-hot-toast';

export default function GuestChatPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const [kbInfo, setKbInfo] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [expired, setExpired] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (!token) { setExpired(true); return; }
    guestAPI.getKB(token)
      .then((res) => setKbInfo(res.data))
      .catch((err) => {
        if (err.response?.status === 410) setExpired(true);
        else toast.error('链接无效');
      });
  }, [token]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const question = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: question }]);
    setLoading(true);
    try {
      const res = await guestAPI.chat({ question, token, top_k: 5 });
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: res.data.answer,
        sources: res.data.sources,
      }]);
    } catch (err) {
      if (err.response?.status === 410) {
        setExpired(true);
      } else {
        setMessages((prev) => [...prev, { role: 'assistant', content: '抱歉，处理问题时出错了。' }]);
      }
    } finally { setLoading(false); }
  };

  if (!token || expired) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', gap: 12 }}>
        <Bot size={64} color="#94a3b8" />
        <h2 style={{ color: '#64748b' }}>分享链接已过期或无效</h2>
        <p style={{ color: '#94a3b8', fontSize: 14 }}>请联系知识库所有者重新生成分享链接</p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: '#f8fafc' }}>
      {/* Header */}
      <div style={{ padding: '16px 24px', background: '#fff', borderBottom: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', gap: 12 }}>
        <Bot size={28} color="var(--primary, #6366f1)" />
        <div>
          <div style={{ fontWeight: 600, fontSize: 16 }}>{kbInfo?.kb_name || '智能问答'}</div>
          <div style={{ fontSize: 12, color: '#94a3b8' }}>
            访客模式 · 链接于 {kbInfo ? new Date(kbInfo.expires_at).toLocaleTimeString() : '--'} 过期
          </div>
        </div>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: 16 }}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: '#94a3b8', marginTop: 80 }}>
            <Bot size={48} style={{ marginBottom: 12 }} />
            <p>你好！请输入问题开始对话</p>
            {kbInfo?.kb_description && <p style={{ fontSize: 13 }}>{kbInfo.kb_description}</p>}
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} style={{ display: 'flex', gap: 10, justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
            {msg.role === 'assistant' && <Bot size={28} color="var(--primary, #6366f1)" style={{ flexShrink: 0, marginTop: 4 }} />}
            <div style={{
              maxWidth: '70%', padding: '12px 16px', borderRadius: 12, fontSize: 14, lineHeight: 1.6,
              background: msg.role === 'user' ? 'var(--primary, #6366f1)' : '#fff',
              color: msg.role === 'user' ? '#fff' : '#1e293b',
              boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
            }}>
              {msg.content}
              {msg.sources?.length > 0 && (
                <div style={{ marginTop: 8, paddingTop: 8, borderTop: '1px solid #e2e8f0', display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                  {msg.sources.map((s, j) => (
                    <span key={j} style={{ fontSize: 11, padding: '2px 8px', background: '#f1f5f9', borderRadius: 8, color: '#64748b' }}>
                      {s.document} ({Math.round(s.relevance_score * 100)}%)
                    </span>
                  ))}
                </div>
              )}
            </div>
            {msg.role === 'user' && <User size={28} color="#94a3b8" style={{ flexShrink: 0, marginTop: 4 }} />}
          </div>
        ))}
        {loading && (
          <div style={{ display: 'flex', gap: 10 }}>
            <Bot size={28} color="var(--primary, #6366f1)" />
            <div style={{ padding: '12px 16px', background: '#fff', borderRadius: 12, boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>
              <Loader size={16} className="spin" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div style={{ padding: '16px 24px', background: '#fff', borderTop: '1px solid #e2e8f0', display: 'flex', gap: 10 }}>
        <input
          style={{ flex: 1, padding: '10px 14px', borderRadius: 8, border: '1px solid #e2e8f0', fontSize: 14, outline: 'none' }}
          placeholder="输入问题..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
          disabled={loading}
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          style={{ padding: '10px 16px', background: 'var(--primary, #6366f1)', color: '#fff', border: 'none', borderRadius: 8, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6 }}
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}
