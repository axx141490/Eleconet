import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { chatAPI } from '../services/api';
import { MessageSquare, Trash2, ArrowRight, History } from 'lucide-react';
import toast from 'react-hot-toast';

export default function ConversationsPage() {
  const [conversations, setConversations] = useState([]);
  const navigate = useNavigate();

  useEffect(() => { loadConversations(); }, []);

  const loadConversations = async () => {
    try {
      const res = await chatAPI.listConversations();
      setConversations(res.data);
    } catch { toast.error('加载对话历史失败'); }
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    if (!confirm('确定要删除该对话？')) return;
    try {
      await chatAPI.deleteConversation(id);
      toast.success('对话已删除');
      loadConversations();
    } catch { toast.error('删除失败'); }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>对话历史</h1>
          <p>查看和管理你的历史对话记录</p>
        </div>
      </div>

      {conversations.length > 0 ? (
        <div className="conv-list">
          {conversations.map((conv) => (
            <div key={conv.id} className="conv-item" onClick={() => navigate(`/chat/${conv.id}`)}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <MessageSquare size={20} color="var(--primary)" />
                <div>
                  <div style={{ fontWeight: 500 }}>{conv.title}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>
                    {new Date(conv.updated_at).toLocaleString()}
                  </div>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <button className="btn btn-sm" style={{ color: 'var(--danger)', padding: 4 }}
                  onClick={(e) => handleDelete(e, conv.id)}>
                  <Trash2 size={16} />
                </button>
                <ArrowRight size={16} color="var(--text-secondary)" />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <History size={64} />
          <h3>暂无对话历史</h3>
          <p>开始一次新的对话后，记录会出现在这里</p>
          <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={() => navigate('/chat')}>
            开始对话
          </button>
        </div>
      )}
    </div>
  );
}
