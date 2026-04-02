import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { kbAPI } from '../services/api';
import { Plus, FileText, Database, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';

export default function KnowledgeBasePage() {
  const [kbs, setKBs] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ name: '', description: '' });
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => { loadKBs(); }, []);

  const loadKBs = async () => {
    try {
      const res = await kbAPI.list();
      setKBs(res.data);
    } catch { toast.error('加载知识库失败'); }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await kbAPI.create(form);
      toast.success('知识库创建成功！');
      setShowModal(false);
      setForm({ name: '', description: '' });
      loadKBs();
    } catch (err) {
      toast.error(err.response?.data?.detail || '创建失败');
    } finally { setLoading(false); }
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    if (!confirm('确定要删除该知识库？此操作不可恢复。')) return;
    try {
      await kbAPI.delete(id);
      toast.success('知识库已删除');
      loadKBs();
    } catch { toast.error('删除失败'); }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>知识库管理</h1>
          <p>创建和管理你的知识库</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          <Plus size={18} /> 新建知识库
        </button>
      </div>

      {kbs.length > 0 ? (
        <div className="card-grid">
          {kbs.map((kb) => (
            <div key={kb.id} className="kb-card" onClick={() => navigate(`/knowledge-base/${kb.id}`)}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <h3>{kb.name}</h3>
                <button className="btn btn-sm" style={{ color: 'var(--danger)', padding: 4 }}
                  onClick={(e) => handleDelete(e, kb.id)}>
                  <Trash2 size={16} />
                </button>
              </div>
              <p className="kb-desc">{kb.description || '暂无描述'}</p>
              <div className="kb-stats">
                <span><FileText size={14} /> {kb.document_count} 文档</span>
                <span>{kb.total_chunks} 向量块</span>
                <span>{new Date(kb.updated_at).toLocaleDateString()}</span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <Database size={64} />
          <h3>还没有知识库</h3>
          <p>点击"新建知识库"创建你的第一个知识库</p>
        </div>
      )}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>新建知识库</h2>
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label>名称</label>
                <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="输入知识库名称" required />
              </div>
              <div className="form-group">
                <label>描述</label>
                <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder="输入知识库描述（可选）" rows={3} />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>取消</button>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? '创建中...' : '创建'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
