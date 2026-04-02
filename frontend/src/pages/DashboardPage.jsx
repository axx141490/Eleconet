import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { statsAPI, kbAPI } from '../services/api';
import { Database, FileText, MessageSquare, Users, ArrowRight } from 'lucide-react';

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [recentKBs, setRecentKBs] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [statsRes, kbRes] = await Promise.all([
        statsAPI.get(),
        kbAPI.list(),
      ]);
      setStats(statsRes.data);
      setRecentKBs(kbRes.data.slice(0, 4));
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    }
  };

  const statItems = stats ? [
    { icon: Database, value: stats.total_knowledge_bases, label: '知识库' },
    { icon: FileText, value: stats.total_documents, label: '文档数量' },
    { icon: MessageSquare, value: stats.total_conversations, label: '对话数' },
    { icon: Users, value: stats.total_users, label: '用户数' },
  ] : [];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>仪表盘</h1>
          <p>欢迎使用 RAG 智能知识库问答系统</p>
        </div>
      </div>

      {stats && (
        <div className="stats-grid">
          {statItems.map((item, i) => (
            <div key={i} className="stat-card">
              <item.icon size={24} color="var(--primary)" style={{ marginBottom: 8 }} />
              <div className="stat-value">{item.value}</div>
              <div className="stat-label">{item.label}</div>
            </div>
          ))}
        </div>
      )}

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <h2 style={{ fontSize: 20 }}>最近的知识库</h2>
        <button className="btn btn-secondary btn-sm" onClick={() => navigate('/knowledge-base')}>
          查看全部 <ArrowRight size={14} />
        </button>
      </div>

      {recentKBs.length > 0 ? (
        <div className="card-grid">
          {recentKBs.map((kb) => (
            <div key={kb.id} className="kb-card" onClick={() => navigate(`/knowledge-base/${kb.id}`)}>
              <h3>{kb.name}</h3>
              <p className="kb-desc">{kb.description || '暂无描述'}</p>
              <div className="kb-stats">
                <span><FileText size={14} /> {kb.document_count} 文档</span>
                <span>{kb.total_chunks} 向量块</span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <Database size={64} />
          <h3>还没有知识库</h3>
          <p>创建你的第一个知识库开始使用</p>
          <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={() => navigate('/knowledge-base')}>
            创建知识库
          </button>
        </div>
      )}

      {stats && (
        <div className="card" style={{ marginTop: 32 }}>
          <h3 style={{ marginBottom: 12 }}>支持的文件格式</h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {stats.supported_formats.map((fmt) => (
              <span key={fmt} style={{
                padding: '4px 12px', background: 'var(--primary-light)', color: 'var(--primary)',
                borderRadius: 20, fontSize: 13, fontWeight: 500,
              }}>
                {fmt}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
