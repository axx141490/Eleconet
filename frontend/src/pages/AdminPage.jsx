import { useState, useEffect } from 'react';
import { adminAPI } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { Shield, Trash2, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';

const ROLE_LABELS = { admin: '管理员', user: '用户' };
const ROLE_COLORS = { admin: '#7c3aed', user: '#2563eb' };
const TIER_LABELS = { free: 'Free', pro: 'Pro', enterprise: 'Enterprise' };
const TIER_COLORS = { free: '#64748b', pro: '#2563eb', enterprise: '#7c3aed' };

export default function AdminPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user?.is_admin) { navigate('/'); return; }
    loadUsers();
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const res = await adminAPI.listUsers();
      setUsers(res.data);
    } catch { toast.error('加载用户失败'); }
    finally { setLoading(false); }
  };

  const handleRoleChange = async (userId, role) => {
    try {
      await adminAPI.updateUser(userId, { role });
      toast.success('角色已更新');
      setUsers((prev) => prev.map((u) => u.id === userId ? { ...u, role, is_admin: role === 'admin' } : u));
    } catch { toast.error('更新失败'); }
  };

  const handleTierChange = async (userId, tier) => {
    const u = users.find((x) => x.id === userId);
    try {
      await adminAPI.updateUser(userId, { role: u.role, tier });
      toast.success('套餐已更新');
      setUsers((prev) => prev.map((x) => x.id === userId ? { ...x, tier } : x));
    } catch { toast.error('更新失败'); }
  };

  const handleToggleActive = async (u) => {
    try {
      await adminAPI.updateUser(u.id, { role: u.role, is_active: !u.is_active });
      toast.success(u.is_active ? '已禁用' : '已启用');
      setUsers((prev) => prev.map((x) => x.id === u.id ? { ...x, is_active: !x.is_active } : x));
    } catch { toast.error('操作失败'); }
  };

  const handleDelete = async (userId) => {
    if (!confirm('确定删除该用户？其知识库和对话记录将一并删除。')) return;
    try {
      await adminAPI.deleteUser(userId);
      toast.success('用户已删除');
      setUsers((prev) => prev.filter((u) => u.id !== userId));
    } catch (err) { toast.error(err.response?.data?.detail || '删除失败'); }
  };

  if (loading) return <div style={{ padding: 32 }}>加载中...</div>;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>用户管理</h1>
          <p>共 {users.length} 个用户</p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={loadUsers}>
          <RefreshCw size={14} /> 刷新
        </button>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
          <thead>
            <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
              <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600, color: '#64748b' }}>用户名</th>
              <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600, color: '#64748b' }}>邮箱</th>
              <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600, color: '#64748b' }}>手机号</th>
              <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600, color: '#64748b' }}>角色</th>
              <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600, color: '#64748b' }}>套餐</th>
              <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600, color: '#64748b' }}>状态</th>
              <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600, color: '#64748b' }}>操作</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                <td style={{ padding: '12px 16px', fontWeight: 500 }}>
                  {u.username}
                  {u.id === user.id && <span style={{ marginLeft: 6, fontSize: 11, color: '#94a3b8' }}>（我）</span>}
                </td>
                <td style={{ padding: '12px 16px', color: '#64748b' }}>{u.email}</td>
                <td style={{ padding: '12px 16px', color: '#64748b', fontFamily: 'monospace' }}>{u.phone || '-'}</td>
                <td style={{ padding: '12px 16px' }}>
                  <select
                    value={u.role}
                    onChange={(e) => handleRoleChange(u.id, e.target.value)}
                    disabled={u.id === user.id}
                    style={{ padding: '4px 8px', borderRadius: 6, border: '1px solid #e2e8f0', fontSize: 13,
                      color: ROLE_COLORS[u.role] || '#374151', background: '#fff', cursor: 'pointer' }}
                  >
                    <option value="user">用户</option>
                    <option value="admin">管理员</option>
                  </select>
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <select
                    value={u.tier || 'free'}
                    onChange={(e) => handleTierChange(u.id, e.target.value)}
                    style={{ padding: '4px 8px', borderRadius: 6, border: '1px solid #e2e8f0', fontSize: 13,
                      color: TIER_COLORS[u.tier || 'free'] || '#374151', background: '#fff', cursor: 'pointer',
                      fontWeight: 600 }}
                  >
                    <option value="free">Free</option>
                    <option value="pro">Pro</option>
                    <option value="enterprise">Enterprise</option>
                  </select>
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <span
                    onClick={() => u.id !== user.id && handleToggleActive(u)}
                    style={{
                      display: 'inline-block', padding: '3px 10px', borderRadius: 12, fontSize: 12, fontWeight: 500,
                      background: u.is_active ? '#dcfce7' : '#fee2e2',
                      color: u.is_active ? '#166534' : '#991b1b',
                      cursor: u.id !== user.id ? 'pointer' : 'default',
                    }}
                  >
                    {u.is_active ? '正常' : '已禁用'}
                  </span>
                </td>
                <td style={{ padding: '12px 16px' }}>
                  {u.id !== user.id && (
                    <button
                      onClick={() => handleDelete(u.id)}
                      style={{ color: '#ef4444', background: 'none', border: 'none', cursor: 'pointer', padding: 4 }}
                    >
                      <Trash2 size={16} />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
