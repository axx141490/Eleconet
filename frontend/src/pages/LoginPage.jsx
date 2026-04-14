import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { authAPI, settingsAPI } from '../services/api';
import toast from 'react-hot-toast';

const RULES = [
  { key: 'len',    label: '至少 8 位',      test: (p) => p.length >= 8 },
  { key: 'upper',  label: '包含大写字母',    test: (p) => /[A-Z]/.test(p) },
  { key: 'lower',  label: '包含小写字母',    test: (p) => /[a-z]/.test(p) },
  { key: 'digit',  label: '包含数字',        test: (p) => /\d/.test(p) },
  { key: 'symbol', label: '包含特殊符号',    test: (p) => /[!@#$%^&*()\-_=+\[\]{};:'",.<>?/\\|`~]/.test(p) },
];

function PasswordStrengthHint({ password }) {
  const passed = RULES.filter((r) => r.test(password)).length;
  const strength = passed <= 2 ? { label: '弱', color: '#ef4444' }
    : passed <= 4 ? { label: '中', color: '#f59e0b' }
    : { label: '强', color: '#22c55e' };

  return (
    <div style={{ marginTop: 8 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
        {[1, 2, 3].map((i) => (
          <div key={i} style={{
            height: 3, flex: 1, borderRadius: 2,
            background: i <= Math.ceil(passed / RULES.length * 3) ? strength.color : '#e2e8f0',
            transition: 'background 0.2s',
          }} />
        ))}
        <span style={{ fontSize: 11, fontWeight: 600, color: strength.color, minWidth: 14 }}>
          {strength.label}
        </span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {RULES.map((r) => {
          const ok = r.test(password);
          return (
            <div key={r.key} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
              <span style={{ color: ok ? '#22c55e' : '#94a3b8', fontSize: 14, lineHeight: 1 }}>
                {ok ? '✓' : '○'}
              </span>
              <span style={{ color: ok ? '#374151' : '#94a3b8' }}>{r.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// 发送验证码按钮（带倒计时）
function SendCodeButton({ phone, scene, onSent }) {
  const [countdown, setCountdown] = useState(0);

  useEffect(() => {
    if (countdown <= 0) return;
    const t = setTimeout(() => setCountdown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [countdown]);

  const handleClick = async () => {
    if (!phone) { toast.error('请先填写手机号'); return; }
    try {
      await authAPI.sendSmsCode(phone, scene);
      toast.success('验证码已发送，5 分钟内有效');
      setCountdown(60);
      onSent?.();
    } catch (err) {
      toast.error(err.response?.data?.detail || '发送失败');
    }
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={countdown > 0}
      style={{
        flexShrink: 0, padding: '0 12px', borderRadius: 8,
        border: '1px solid var(--border)', background: countdown > 0 ? '#f3f4f6' : '#fff',
        fontSize: 13, cursor: countdown > 0 ? 'default' : 'pointer',
        color: countdown > 0 ? '#94a3b8' : 'var(--primary)', whiteSpace: 'nowrap',
      }}
    >
      {countdown > 0 ? `${countdown}s` : '发送验证码'}
    </button>
  );
}

export default function LoginPage() {
  const [mode, setMode] = useState('login');        // login | register
  const [loginTab, setLoginTab] = useState('pwd');  // pwd | sms
  const [form, setForm] = useState({ username: '', email: '', password: '', phone: '', sms_code: '' });
  const [loading, setLoading] = useState(false);
  const [smsCfg, setSmsCfg] = useState({ enabled: false, require_phone_on_register: false });
  const { login, loginSms, register } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    settingsAPI.getSmsStatus().then((res) => setSmsCfg(res.data)).catch(() => {});
  }, []);

  const isRegister = mode === 'register';
  const showPhone = isRegister && smsCfg.enabled;
  const requirePhone = isRegister && smsCfg.enabled && smsCfg.require_phone_on_register;

  const handleSubmit = async (e) => {
    e.preventDefault();

    // 注册校验
    if (isRegister) {
      const failed = RULES.filter((r) => !r.test(form.password)).map((r) => r.label);
      if (failed.length) { toast.error('密码需满足：' + failed.join('、')); return; }
      if (requirePhone && !form.phone) { toast.error('请填写手机号'); return; }
      if (requirePhone && !form.sms_code) { toast.error('请填写短信验证码'); return; }
    }

    // 短信登录校验
    if (!isRegister && loginTab === 'sms') {
      if (!form.phone) { toast.error('请填写手机号'); return; }
      if (!form.sms_code) { toast.error('请填写验证码'); return; }
    }

    setLoading(true);
    try {
      if (isRegister) {
        await register(form.username, form.email, form.password, form.phone || undefined, form.sms_code || undefined);
        toast.success('注册成功！');
      } else if (loginTab === 'sms') {
        await loginSms(form.phone, form.sms_code);
        toast.success('登录成功！');
      } else {
        await login(form.username, form.password);
        toast.success('登录成功！');
      }
      navigate('/');
    } catch (err) {
      toast.error(err.response?.data?.detail || '操作失败');
    } finally {
      setLoading(false);
    }
  };

  const tabStyle = (active) => ({
    flex: 1, padding: '8px 0', fontSize: 14, fontWeight: active ? 600 : 400,
    border: 'none', background: 'none', cursor: 'pointer',
    color: active ? 'var(--primary)' : '#94a3b8',
    borderBottom: `2px solid ${active ? 'var(--primary)' : 'transparent'}`,
    transition: 'all 0.15s',
  });

  return (
    <div className="login-page">
      <div className="login-card">
        <h1>{isRegister ? '注册' : '登录'}</h1>
        <p className="subtitle">RAG 智能知识库问答系统</p>

        {/* 登录模式下的 Tab（仅在 SMS 启用时显示） */}
        {!isRegister && smsCfg.enabled && (
          <div style={{ display: 'flex', marginBottom: 20, borderBottom: '1px solid var(--border)' }}>
            <button style={tabStyle(loginTab === 'pwd')} onClick={() => setLoginTab('pwd')}>密码登录</button>
            <button style={tabStyle(loginTab === 'sms')} onClick={() => setLoginTab('sms')}>短信登录</button>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* 密码登录 / 注册 */}
          {(isRegister || loginTab === 'pwd') && (
            <>
              <div className="form-group">
                <label>用户名</label>
                <input
                  type="text"
                  value={form.username}
                  onChange={(e) => setForm({ ...form, username: e.target.value })}
                  placeholder={isRegister ? '请输入用户名' : '用户名 / 邮箱 / 手机号'}
                  required
                />
              </div>
              {isRegister && (
                <div className="form-group">
                  <label>邮箱</label>
                  <input
                    type="email"
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    placeholder="请输入邮箱"
                    required
                  />
                </div>
              )}
              {showPhone && (
                <div className="form-group">
                  <label>手机号{!requirePhone && <span style={{ fontSize: 12, color: '#94a3b8', marginLeft: 4 }}>（选填）</span>}</label>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <input
                      type="tel"
                      value={form.phone}
                      onChange={(e) => setForm({ ...form, phone: e.target.value })}
                      placeholder="请输入手机号"
                      required={requirePhone}
                      style={{ flex: 1 }}
                    />
                    <SendCodeButton phone={form.phone} scene="register" />
                  </div>
                </div>
              )}
              {showPhone && form.phone && (
                <div className="form-group">
                  <label>短信验证码{!requirePhone && <span style={{ fontSize: 12, color: '#94a3b8', marginLeft: 4 }}>（选填）</span>}</label>
                  <input
                    type="text"
                    value={form.sms_code}
                    onChange={(e) => setForm({ ...form, sms_code: e.target.value })}
                    placeholder="6 位验证码"
                    maxLength={6}
                    required={requirePhone}
                  />
                </div>
              )}
              <div className="form-group">
                <label>密码</label>
                <input
                  type="password"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  placeholder="请输入密码"
                  required
                  minLength={8}
                />
                {isRegister && form.password.length > 0 && (
                  <PasswordStrengthHint password={form.password} />
                )}
              </div>
            </>
          )}

          {/* 短信登录 */}
          {!isRegister && loginTab === 'sms' && (
            <>
              <div className="form-group">
                <label>手机号</label>
                <div style={{ display: 'flex', gap: 8 }}>
                  <input
                    type="tel"
                    value={form.phone}
                    onChange={(e) => setForm({ ...form, phone: e.target.value })}
                    placeholder="请输入手机号"
                    required
                    style={{ flex: 1 }}
                  />
                  <SendCodeButton phone={form.phone} scene="login" />
                </div>
              </div>
              <div className="form-group">
                <label>验证码</label>
                <input
                  type="text"
                  value={form.sms_code}
                  onChange={(e) => setForm({ ...form, sms_code: e.target.value })}
                  placeholder="6 位验证码"
                  maxLength={6}
                  required
                />
              </div>
            </>
          )}

          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? <><span className="spinner" /> 处理中...</> : (isRegister ? '注册' : '登录')}
            </button>
          </div>
        </form>

        <div className="form-toggle">
          {isRegister ? '已有账号？' : '没有账号？'}
          <a href="#" onClick={(e) => { e.preventDefault(); setMode(isRegister ? 'login' : 'register'); }}>
            {isRegister ? '立即登录' : '立即注册'}
          </a>
        </div>
      </div>
    </div>
  );
}
