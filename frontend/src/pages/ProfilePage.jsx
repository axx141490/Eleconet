import { useState } from 'react';
import { authAPI } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { KeyRound, Mail, Save, Eye, EyeOff } from 'lucide-react';
import toast from 'react-hot-toast';

const inputStyle = {
  width: '100%', padding: '9px 12px', borderRadius: 8,
  border: '1px solid #e2e8f0', fontSize: 14, boxSizing: 'border-box',
  outline: 'none',
};

function PasswordInput({ value, onChange, placeholder }) {
  const [show, setShow] = useState(false);
  return (
    <div style={{ position: 'relative' }}>
      <input
        type={show ? 'text' : 'password'}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        style={{ ...inputStyle, paddingRight: 40 }}
      />
      <button
        type="button"
        onClick={() => setShow((v) => !v)}
        style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)',
          background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', padding: 0 }}
      >
        {show ? <EyeOff size={16} /> : <Eye size={16} />}
      </button>
    </div>
  );
}

function ChangeEmailSection({ user, onUpdated }) {
  const [newEmail, setNewEmail] = useState('');
  const [password, setPassword] = useState('');
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!newEmail.trim()) { toast.error('请输入新邮箱'); return; }
    if (!newEmail.includes('@')) { toast.error('邮箱格式不正确'); return; }
    if (!password) { toast.error('请输入当前密码'); return; }
    setSaving(true);
    try {
      const res = await authAPI.changeEmail({ new_email: newEmail.trim(), current_password: password });
      toast.success('邮箱已更新');
      setNewEmail('');
      setPassword('');
      onUpdated(res.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || '更新失败');
    } finally { setSaving(false); }
  };

  return (
    <div className="card" style={{ marginBottom: 20 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
        <Mail size={18} color="#6366f1" />
        <h3 style={{ fontSize: 16, margin: 0 }}>更换邮箱</h3>
      </div>

      <div style={{ marginBottom: 12 }}>
        <label style={{ display: 'block', fontSize: 13, color: '#64748b', marginBottom: 5 }}>当前邮箱</label>
        <input value={user.email} disabled style={{ ...inputStyle, background: '#f8fafc', color: '#94a3b8' }} />
      </div>

      <div style={{ marginBottom: 12 }}>
        <label style={{ display: 'block', fontSize: 13, color: '#64748b', marginBottom: 5 }}>新邮箱</label>
        <input
          type="email"
          value={newEmail}
          onChange={(e) => setNewEmail(e.target.value)}
          placeholder="输入新邮箱地址"
          style={inputStyle}
        />
      </div>

      <div style={{ marginBottom: 16 }}>
        <label style={{ display: 'block', fontSize: 13, color: '#64748b', marginBottom: 5 }}>当前密码（验证身份）</label>
        <PasswordInput value={password} onChange={(e) => setPassword(e.target.value)} placeholder="输入当前密码" />
      </div>

      <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
        <Save size={14} /> {saving ? '保存中...' : '保存'}
      </button>
    </div>
  );
}

function ChangePasswordSection() {
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!current) { toast.error('请输入当前密码'); return; }
    const errs = [];
    if (next.length < 8) errs.push('至少 8 位');
    if (!/[A-Z]/.test(next)) errs.push('至少一个大写字母');
    if (!/[a-z]/.test(next)) errs.push('至少一个小写字母');
    if (!/\d/.test(next)) errs.push('至少一个数字');
    if (!/[!@#$%^&*()\-_=+\[\]{};:'",.<>?/\\|`~]/.test(next)) errs.push('至少一个特殊符号');
    if (errs.length) { toast.error('密码需满足：' + errs.join('、')); return; }
    if (next !== confirm) { toast.error('两次输入的新密码不一致'); return; }
    setSaving(true);
    try {
      await authAPI.changePassword({ current_password: current, new_password: next });
      toast.success('密码已修改，下次登录使用新密码');
      setCurrent(''); setNext(''); setConfirm('');
    } catch (err) {
      toast.error(err.response?.data?.detail || '修改失败');
    } finally { setSaving(false); }
  };

  const passedRules = next.length === 0 ? 0 : [
    next.length >= 8,
    /[A-Z]/.test(next),
    /[a-z]/.test(next),
    /\d/.test(next),
    /[!@#$%^&*()\-_=+\[\]{};:'",.<>?/\\|`~]/.test(next),
  ].filter(Boolean).length;
  const strength = next.length === 0 ? null : passedRules <= 2 ? 'weak' : passedRules <= 4 ? 'medium' : 'strong';
  const strengthMap = { weak: ['#ef4444', '弱'], medium: ['#f59e0b', '中'], strong: ['#22c55e', '强'] };

  return (
    <div className="card">
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
        <KeyRound size={18} color="#6366f1" />
        <h3 style={{ fontSize: 16, margin: 0 }}>修改密码</h3>
      </div>

      <div style={{ marginBottom: 12 }}>
        <label style={{ display: 'block', fontSize: 13, color: '#64748b', marginBottom: 5 }}>当前密码</label>
        <PasswordInput value={current} onChange={(e) => setCurrent(e.target.value)} placeholder="输入当前密码" />
      </div>

      <div style={{ marginBottom: 12 }}>
        <label style={{ display: 'block', fontSize: 13, color: '#64748b', marginBottom: 5 }}>新密码</label>
        <PasswordInput value={next} onChange={(e) => setNext(e.target.value)} placeholder="大小写字母 + 数字 + 符号，至少 8 位" />
        {strength && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 6 }}>
            {['weak', 'medium', 'strong'].map((s) => (
              <div key={s} style={{
                height: 3, flex: 1, borderRadius: 2,
                background: ['weak', 'medium', 'strong'].indexOf(s) <= ['weak', 'medium', 'strong'].indexOf(strength)
                  ? strengthMap[strength][0] : '#e2e8f0',
              }} />
            ))}
            <span style={{ fontSize: 11, color: strengthMap[strength][0], fontWeight: 600 }}>
              {strengthMap[strength][1]}
            </span>
          </div>
        )}
      </div>

      <div style={{ marginBottom: 16 }}>
        <label style={{ display: 'block', fontSize: 13, color: '#64748b', marginBottom: 5 }}>确认新密码</label>
        <PasswordInput value={confirm} onChange={(e) => setConfirm(e.target.value)} placeholder="再次输入新密码" />
        {confirm && next !== confirm && (
          <p style={{ fontSize: 12, color: '#ef4444', margin: '4px 0 0' }}>两次密码不一致</p>
        )}
      </div>

      <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
        <Save size={14} /> {saving ? '保存中...' : '保存'}
      </button>
    </div>
  );
}

export default function ProfilePage() {
  const { user, refreshUser } = useAuth();

  const handleEmailUpdated = async () => {
    if (refreshUser) await refreshUser();
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>个人设置</h1>
          <p>管理你的账号信息和登录方式</p>
        </div>
      </div>

      <div style={{ maxWidth: 520 }}>
        <ChangeEmailSection user={user} onUpdated={handleEmailUpdated} />
        <ChangePasswordSection />
      </div>
    </div>
  );
}
