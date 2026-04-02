import { useState, useRef, useEffect } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import {
  LayoutDashboard, Database, MessageSquare, History, LogOut, Settings, ShieldCheck, Zap,
  Mail, Shield, Clock, ChevronUp, UserCog,
} from 'lucide-react';

const baseNavItems = [
  { path: '/', icon: LayoutDashboard, label: '仪表盘' },
  { path: '/knowledge-base', icon: Database, label: '知识库' },
  { path: '/chat', icon: MessageSquare, label: '智能问答' },
  { path: '/conversations', icon: History, label: '对话历史' },
];

const adminNavItems = [
  { path: '/settings', icon: Settings, label: '模型配置' },
  { path: '/admin', icon: ShieldCheck, label: '用户管理' },
];

const TIER_COLORS = {
  enterprise: '#7c3aed',
  pro: '#2563eb',
  free: '#64748b',
};

const TIER_LABELS = {
  enterprise: 'Enterprise',
  pro: 'Pro',
  free: 'Free',
};

function UserProfilePopup({ user, onClose, onLogout }) {
  const navigate = useNavigate();
  const ref = useRef(null);

  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) onClose(); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [onClose]);

  const tierColor = TIER_COLORS[user.tier] || '#64748b';
  const expiresAt = user.tier_expires_at ? new Date(user.tier_expires_at) : null;
  const daysLeft = expiresAt ? Math.ceil((expiresAt - Date.now()) / 86400000) : null;

  return (
    <div ref={ref} style={{
      position: 'absolute', bottom: 72, left: 12, right: 12,
      background: '#fff', borderRadius: 12, boxShadow: '0 -4px 24px rgba(0,0,0,0.18)',
      overflow: 'hidden', zIndex: 100,
    }}>
      {/* Header */}
      <div style={{ background: `linear-gradient(135deg, ${tierColor}22, ${tierColor}11)`, padding: '16px 16px 12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 40, height: 40, borderRadius: '50%',
            background: tierColor, display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 18, fontWeight: 700, color: '#fff', flexShrink: 0,
          }}>
            {user.username[0].toUpperCase()}
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: 14, color: '#1e293b' }}>{user.username}</div>
            <span style={{
              fontSize: 10, fontWeight: 700, padding: '1px 8px', borderRadius: 8,
              background: tierColor, color: '#fff', letterSpacing: 0.5,
            }}>
              {TIER_LABELS[user.tier] || user.tier.toUpperCase()}
            </span>
          </div>
        </div>
      </div>

      {/* Info rows */}
      <div style={{ padding: '8px 0' }}>
        <div style={{ padding: '7px 16px', display: 'flex', alignItems: 'center', gap: 10, fontSize: 13, color: '#374151' }}>
          <Mail size={14} color="#94a3b8" style={{ flexShrink: 0 }} />
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{user.email}</span>
        </div>

        <div style={{ padding: '7px 16px', display: 'flex', alignItems: 'center', gap: 10, fontSize: 13, color: '#374151' }}>
          <Shield size={14} color="#94a3b8" style={{ flexShrink: 0 }} />
          <span>{user.is_admin ? '管理员' : '普通用户'}</span>
        </div>

        {expiresAt && user.tier !== 'free' && (
          <div style={{ padding: '7px 16px', display: 'flex', alignItems: 'center', gap: 10, fontSize: 13 }}>
            <Clock size={14} color="#94a3b8" style={{ flexShrink: 0 }} />
            <span style={{ color: daysLeft <= 7 ? '#ef4444' : '#374151' }}>
              套餐到期：{expiresAt.toLocaleDateString('zh-CN')}
              {daysLeft !== null && (
                <span style={{ marginLeft: 6, fontSize: 11,
                  color: daysLeft <= 7 ? '#ef4444' : '#94a3b8' }}>
                  （{daysLeft > 0 ? `还剩 ${daysLeft} 天` : '已到期'}）
                </span>
              )}
            </span>
          </div>
        )}

        {user.tier === 'free' && (
          <div style={{ padding: '7px 16px', display: 'flex', alignItems: 'center', gap: 10, fontSize: 13, color: '#64748b' }}>
            <Clock size={14} color="#94a3b8" style={{ flexShrink: 0 }} />
            <span>免费套餐（永久有效）</span>
          </div>
        )}
      </div>

      <div style={{ borderTop: '1px solid #f1f5f9', padding: '8px' }}>
        <button onClick={() => { navigate('/profile'); onClose(); }} style={{
          width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid #e2e8f0',
          background: '#fff', color: '#374151', fontSize: 13, cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
          marginBottom: 4,
        }}>
          <UserCog size={13} /> 个人设置
        </button>
        {user.tier !== 'enterprise' && (
          <button onClick={() => { navigate('/pricing'); onClose(); }} style={{
            width: '100%', padding: '8px 12px', borderRadius: 8, border: 'none',
            background: `linear-gradient(90deg, #6366f1, #7c3aed)`,
            color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
            marginBottom: 4,
          }}>
            <Zap size={13} /> 升级套餐
          </button>
        )}
        <button onClick={onLogout} style={{
          width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid #e2e8f0',
          background: '#fff', color: '#64748b', fontSize: 13, cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
        }}>
          <LogOut size={13} /> 退出登录
        </button>
      </div>
    </div>
  );
}

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [showProfile, setShowProfile] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="app-layout">
      <aside className="sidebar" style={{ position: 'relative' }}>
        <div className="sidebar-logo">RAG 智能知识库</div>
        <nav className="sidebar-nav">
          {baseNavItems.map((item) => (
            <NavLink key={item.path} to={item.path} end={item.path === '/'}
              className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
              <item.icon />{item.label}
            </NavLink>
          ))}
          {user?.is_admin && (
            <>
              <div style={{ margin: '8px 0', borderTop: '1px solid rgba(255,255,255,0.1)' }} />
              {adminNavItems.map((item) => (
                <NavLink key={item.path} to={item.path}
                  className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
                  <item.icon />{item.label}
                </NavLink>
              ))}
            </>
          )}
          {user && user.tier !== 'enterprise' && (
            <>
              <div style={{ margin: '8px 0', borderTop: '1px solid rgba(255,255,255,0.1)' }} />
              <NavLink to="/pricing"
                className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
                style={{ background: 'linear-gradient(90deg,#6366f1,#7c3aed)', borderRadius: 8 }}>
                <Zap size={16} /> 升级套餐
              </NavLink>
            </>
          )}
        </nav>

        {/* User profile popup */}
        {showProfile && user && (
          <UserProfilePopup
            user={user}
            onClose={() => setShowProfile(false)}
            onLogout={handleLogout}
          />
        )}

        <div className="sidebar-footer">
          <button
            onClick={() => setShowProfile((v) => !v)}
            style={{
              width: '100%', background: showProfile ? 'rgba(255,255,255,0.08)' : 'transparent',
              border: 'none', borderRadius: 8, padding: '8px 10px', cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: 8, color: '#fff',
            }}
          >
            <div style={{
              width: 30, height: 30, borderRadius: '50%', flexShrink: 0,
              background: TIER_COLORS[user?.tier] || '#64748b',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 13, fontWeight: 700, color: '#fff',
            }}>
              {user?.username?.[0]?.toUpperCase()}
            </div>
            <div style={{ flex: 1, textAlign: 'left', minWidth: 0 }}>
              <div style={{ fontSize: 13, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {user?.username}
              </div>
              <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                {TIER_LABELS[user?.tier] || user?.tier}
              </div>
            </div>
            <ChevronUp size={14} color="rgba(255,255,255,0.4)"
              style={{ transform: showProfile ? 'rotate(0deg)' : 'rotate(180deg)', transition: 'transform 0.2s' }} />
          </button>
        </div>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
