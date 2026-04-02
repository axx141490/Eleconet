import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import toast from 'react-hot-toast';

export default function LoginPage() {
  const [isRegister, setIsRegister] = useState(false);
  const [form, setForm] = useState({ username: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (isRegister) {
        await register(form.username, form.email, form.password);
        toast.success('注册成功！');
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

  return (
    <div className="login-page">
      <div className="login-card">
        <h1>{isRegister ? '注册' : '登录'}</h1>
        <p className="subtitle">RAG 智能知识库问答系统</p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>用户名</label>
            <input
              type="text"
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              placeholder="请输入用户名"
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
          <div className="form-group">
            <label>密码</label>
            <input
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              placeholder="请输入密码"
              required
              minLength={6}
            />
          </div>
          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? <><span className="spinner" /> 处理中...</> : (isRegister ? '注册' : '登录')}
            </button>
          </div>
        </form>
        <div className="form-toggle">
          {isRegister ? '已有账号？' : '没有账号？'}
          <a href="#" onClick={(e) => { e.preventDefault(); setIsRegister(!isRegister); }}>
            {isRegister ? '立即登录' : '立即注册'}
          </a>
        </div>
      </div>
    </div>
  );
}
