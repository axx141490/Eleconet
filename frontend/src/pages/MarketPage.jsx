import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { marketAPI } from '../services/api';
import { Plus, Trash2, Store, Tag, BookOpen, Edit2, Check, X } from 'lucide-react';
import toast from 'react-hot-toast';

const CATEGORIES = ['全部', '通用', '医疗', '法律', '金融', '教育', '电商', '技术', '其他'];

const CATEGORY_COLORS = {
  通用: '#64748b', 医疗: '#0ea5e9', 法律: '#7c3aed', 金融: '#f59e0b',
  教育: '#22c55e', 电商: '#ec4899', 技术: '#6366f1', 其他: '#94a3b8',
};

function TemplateCard({ tpl, isAdmin, onUse, onDelete, onEdit }) {
  const tagList = tpl.tags ? tpl.tags.split(',').map((t) => t.trim()).filter(Boolean) : [];
  const catColor = CATEGORY_COLORS[tpl.category] || '#64748b';

  return (
    <div style={{
      background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0',
      padding: 20, display: 'flex', flexDirection: 'column', gap: 12,
      opacity: tpl.is_active ? 1 : 0.5, position: 'relative',
      transition: 'box-shadow 0.15s',
    }}
      onMouseEnter={(e) => e.currentTarget.style.boxShadow = '0 4px 20px rgba(0,0,0,0.08)'}
      onMouseLeave={(e) => e.currentTarget.style.boxShadow = 'none'}
    >
      {!tpl.is_active && (
        <span style={{
          position: 'absolute', top: 10, right: 10, fontSize: 11, padding: '2px 8px',
          borderRadius: 6, background: '#fef2f2', color: '#ef4444', fontWeight: 600,
        }}>已下架</span>
      )}

      {/* Category badge */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{
          fontSize: 11, fontWeight: 700, padding: '2px 10px', borderRadius: 20,
          background: catColor + '22', color: catColor,
        }}>{tpl.category}</span>
        {tpl.use_count > 0 && (
          <span style={{ fontSize: 11, color: '#94a3b8' }}>已被使用 {tpl.use_count} 次</span>
        )}
      </div>

      <div>
        <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600, color: '#1e293b' }}>{tpl.name}</h3>
        <p style={{ margin: '6px 0 0', fontSize: 13, color: '#64748b', lineHeight: 1.5 }}>
          {tpl.description || '暂无描述'}
        </p>
      </div>

      {tagList.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {tagList.map((tag) => (
            <span key={tag} style={{
              fontSize: 11, padding: '2px 8px', borderRadius: 12,
              background: '#f1f5f9', color: '#475569',
            }}>
              <Tag size={9} style={{ marginRight: 3, verticalAlign: 'middle' }} />{tag}
            </span>
          ))}
        </div>
      )}

      {tpl.sample_docs_hint && (
        <div style={{
          background: '#f8fafc', borderRadius: 8, padding: '8px 12px',
          fontSize: 12, color: '#64748b', lineHeight: 1.5,
        }}>
          <BookOpen size={12} style={{ marginRight: 4, verticalAlign: 'middle' }} />
          <strong>建议上传：</strong>{tpl.sample_docs_hint}
        </div>
      )}

      <div style={{ display: 'flex', gap: 8, marginTop: 'auto' }}>
        {tpl.is_active && (
          <button className="btn btn-primary" style={{ flex: 1, fontSize: 13 }} onClick={() => onUse(tpl)}>
            使用此模板
          </button>
        )}
        {isAdmin && (
          <>
            <button className="btn btn-sm" style={{ padding: '6px 10px' }} onClick={() => onEdit(tpl)} title="编辑">
              <Edit2 size={14} />
            </button>
            <button className="btn btn-sm" style={{ padding: '6px 10px', color: 'var(--danger)' }}
              onClick={() => onDelete(tpl.id)} title="删除">
              <Trash2 size={14} />
            </button>
          </>
        )}
      </div>
    </div>
  );
}

function CreateModal({ onClose, onCreated }) {
  const [form, setForm] = useState({
    name: '', description: '', category: '通用',
    tags: '', sample_docs_hint: '', is_active: true,
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) { toast.error('请填写模板名称'); return; }
    setLoading(true);
    try {
      const res = await marketAPI.create(form);
      toast.success('模板创建成功');
      onCreated(res.data);
      onClose();
    } catch (err) {
      toast.error(err.response?.data?.detail || '创建失败');
    } finally { setLoading(false); }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" style={{ maxWidth: 520 }} onClick={(e) => e.stopPropagation()}>
        <h2>新建知识库模板</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>模板名称 *</label>
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="如：法律合同知识库" required />
          </div>
          <div className="form-group">
            <label>所属分类</label>
            <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}
              style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--border)' }}>
              {CATEGORIES.filter((c) => c !== '全部').map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>描述</label>
            <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="简要介绍此模板的用途和适用场景" rows={2} />
          </div>
          <div className="form-group">
            <label>标签 <span style={{ fontSize: 12, color: '#94a3b8' }}>（逗号分隔）</span></label>
            <input value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })}
              placeholder="如：合同,劳务,知识产权" />
          </div>
          <div className="form-group">
            <label>建议上传文档</label>
            <textarea value={form.sample_docs_hint} onChange={(e) => setForm({ ...form, sample_docs_hint: e.target.value })}
              placeholder="告诉用户该知识库适合上传哪些类型的文档" rows={2} />
          </div>
          <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <input type="checkbox" id="is_active" checked={form.is_active}
              onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
            <label htmlFor="is_active" style={{ margin: 0, cursor: 'pointer' }}>立即上架（对所有用户可见）</label>
          </div>
          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>取消</button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? '创建中...' : '创建模板'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function EditModal({ tpl, onClose, onSaved }) {
  const [form, setForm] = useState({
    name: tpl.name, description: tpl.description, category: tpl.category,
    tags: tpl.tags, sample_docs_hint: tpl.sample_docs_hint, is_active: tpl.is_active,
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await marketAPI.update(tpl.id, form);
      toast.success('模板已更新');
      onSaved(res.data);
      onClose();
    } catch (err) {
      toast.error(err.response?.data?.detail || '更新失败');
    } finally { setLoading(false); }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" style={{ maxWidth: 520 }} onClick={(e) => e.stopPropagation()}>
        <h2>编辑模板</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>模板名称 *</label>
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>所属分类</label>
            <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}
              style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--border)' }}>
              {CATEGORIES.filter((c) => c !== '全部').map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>描述</label>
            <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={2} />
          </div>
          <div className="form-group">
            <label>标签 <span style={{ fontSize: 12, color: '#94a3b8' }}>（逗号分隔）</span></label>
            <input value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} />
          </div>
          <div className="form-group">
            <label>建议上传文档</label>
            <textarea value={form.sample_docs_hint} onChange={(e) => setForm({ ...form, sample_docs_hint: e.target.value })} rows={2} />
          </div>
          <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <input type="checkbox" id="edit_is_active" checked={form.is_active}
              onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
            <label htmlFor="edit_is_active" style={{ margin: 0, cursor: 'pointer' }}>已上架（对所有用户可见）</label>
          </div>
          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>取消</button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? '保存中...' : '保存'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Hint dialog shown after using a template
function HintDialog({ hint, kbId, onClose }) {
  const navigate = useNavigate();
  return (
    <div className="modal-overlay">
      <div className="modal" style={{ maxWidth: 460 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
          <Check size={20} color="#22c55e" />
          <h2 style={{ margin: 0 }}>知识库创建成功</h2>
        </div>
        {hint && (
          <div style={{
            background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 8,
            padding: '10px 14px', fontSize: 13, color: '#166534', marginBottom: 16, lineHeight: 1.6,
          }}>
            <strong>建议上传的文档：</strong><br />{hint}
          </div>
        )}
        <p style={{ color: '#64748b', fontSize: 13, marginBottom: 20 }}>
          前往知识库页面上传文档，完成知识库搭建。
        </p>
        <div className="modal-actions">
          <button className="btn btn-secondary" onClick={onClose}>稍后上传</button>
          <button className="btn btn-primary" onClick={() => navigate(`/knowledge-base/${kbId}`)}>
            立即上传文档
          </button>
        </div>
      </div>
    </div>
  );
}

export default function MarketPage() {
  const { user } = useAuth();
  const [templates, setTemplates] = useState([]);
  const [activeCategory, setActiveCategory] = useState('全部');
  const [showCreate, setShowCreate] = useState(false);
  const [editTpl, setEditTpl] = useState(null);
  const [hintDialog, setHintDialog] = useState(null);  // { kbId, hint }
  const [using, setUsing] = useState(null);

  const isAdmin = user?.is_admin;

  useEffect(() => { loadTemplates(); }, []);

  const loadTemplates = async () => {
    try {
      const res = await marketAPI.list();
      setTemplates(res.data);
    } catch { toast.error('加载模板失败'); }
  };

  const handleUse = async (tpl) => {
    if (using) return;
    setUsing(tpl.id);
    try {
      const res = await marketAPI.use(tpl.id);
      const { kb_id, sample_docs_hint } = res.data;
      setHintDialog({ kbId: kb_id, hint: sample_docs_hint });
      loadTemplates();  // refresh use_count
    } catch (err) {
      toast.error(err.response?.data?.detail || '使用失败');
    } finally { setUsing(null); }
  };

  const handleDelete = async (id) => {
    if (!confirm('确定删除此模板？')) return;
    try {
      await marketAPI.delete(id);
      toast.success('模板已删除');
      setTemplates((prev) => prev.filter((t) => t.id !== id));
    } catch (err) {
      toast.error(err.response?.data?.detail || '删除失败');
    }
  };

  const displayed = templates.filter(
    (t) => activeCategory === '全部' || t.category === activeCategory
  );

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>知识库市场</h1>
          <p>选择行业模板，快速搭建专属知识库</p>
        </div>
        {isAdmin && (
          <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
            <Plus size={18} /> 新建模板
          </button>
        )}
      </div>

      {/* Category filter */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 24 }}>
        {CATEGORIES.map((cat) => {
          const count = cat === '全部'
            ? templates.length
            : templates.filter((t) => t.category === cat).length;
          if (count === 0 && cat !== '全部' && !isAdmin) return null;
          return (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              style={{
                padding: '6px 16px', borderRadius: 20, border: '1px solid',
                fontSize: 13, cursor: 'pointer', transition: 'all 0.15s',
                borderColor: activeCategory === cat ? 'var(--primary)' : '#e2e8f0',
                background: activeCategory === cat ? 'var(--primary)' : '#fff',
                color: activeCategory === cat ? '#fff' : '#475569',
                fontWeight: activeCategory === cat ? 600 : 400,
              }}
            >
              {cat} {count > 0 && <span style={{ opacity: 0.7, fontSize: 11 }}>({count})</span>}
            </button>
          );
        })}
      </div>

      {displayed.length > 0 ? (
        <div className="card-grid">
          {displayed.map((tpl) => (
            <TemplateCard
              key={tpl.id}
              tpl={tpl}
              isAdmin={isAdmin}
              onUse={handleUse}
              onDelete={handleDelete}
              onEdit={setEditTpl}
            />
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <Store size={64} />
          <h3>{activeCategory === '全部' ? '暂无模板' : `暂无「${activeCategory}」分类模板`}</h3>
          {isAdmin && <p>点击右上角"新建模板"添加第一个模板</p>}
        </div>
      )}

      {showCreate && (
        <CreateModal
          onClose={() => setShowCreate(false)}
          onCreated={(tpl) => setTemplates((prev) => [...prev, tpl])}
        />
      )}

      {editTpl && (
        <EditModal
          tpl={editTpl}
          onClose={() => setEditTpl(null)}
          onSaved={(updated) => {
            setTemplates((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
          }}
        />
      )}

      {hintDialog && (
        <HintDialog
          hint={hintDialog.hint}
          kbId={hintDialog.kbId}
          onClose={() => setHintDialog(null)}
        />
      )}
    </div>
  );
}
