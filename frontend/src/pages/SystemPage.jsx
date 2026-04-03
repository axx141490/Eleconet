import { useState, useEffect } from 'react';
import { settingsAPI, paymentAPI } from '../services/api';
import { Save, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';

const inputStyle = { width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border)', fontSize: 14, boxSizing: 'border-box' };

// ─── 支付配置 ────────────────────────────────────────────────
function PaymentConfigSection() {
  const s = { width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border)', fontSize: 13, boxSizing: 'border-box' };
  const [cfg, setCfg] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    paymentAPI.getConfig().then((res) => setCfg(res.data)).catch(() => {});
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await paymentAPI.updateConfig(cfg);
      toast.success('支付配置已保存');
    } catch { toast.error('保存失败'); }
    finally { setSaving(false); }
  };

  if (!cfg) return null;

  const priceField = (label, key) => (
    <div>
      <label style={{ display: 'block', marginBottom: 4, fontSize: 12, color: 'var(--text-secondary)' }}>{label}（分，100=¥1）</label>
      <input type="number" value={cfg.pricing[key] || 0} style={s}
        onChange={(e) => setCfg({ ...cfg, pricing: { ...cfg.pricing, [key]: parseInt(e.target.value) } })} />
    </div>
  );
  const wcField = (label, key, type = 'text') => (
    <div>
      <label style={{ display: 'block', marginBottom: 4, fontSize: 12, color: 'var(--text-secondary)' }}>{label}</label>
      <input type={type} value={cfg.wechat[key] || ''} placeholder={key.includes('key') ? '已设置则留空' : ''} style={s}
        onChange={(e) => setCfg({ ...cfg, wechat: { ...cfg.wechat, [key]: e.target.value } })} />
    </div>
  );
  const apField = (label, key, type = 'text') => (
    <div>
      <label style={{ display: 'block', marginBottom: 4, fontSize: 12, color: 'var(--text-secondary)' }}>{label}</label>
      <input type={type} value={cfg.alipay[key] || ''} placeholder={key.includes('key') ? '已设置则留空' : ''} style={s}
        onChange={(e) => setCfg({ ...cfg, alipay: { ...cfg.alipay, [key]: e.target.value } })} />
    </div>
  );

  return (
    <div className="card" style={{ marginBottom: 24 }}>
      <h3 style={{ fontSize: 16, marginBottom: 16 }}>支付配置</h3>

      <h4 style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 12 }}>定价（单位：分）</h4>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 20 }}>
        {priceField('Pro 月付', 'pro_monthly')}
        {priceField('Pro 年付', 'pro_yearly')}
        {priceField('Enterprise 月付', 'enterprise_monthly')}
        {priceField('Enterprise 年付', 'enterprise_yearly')}
      </div>

      <h4 style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 8 }}>微信支付</h4>
      <label style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12, fontSize: 14, cursor: 'pointer' }}>
        <input type="checkbox" checked={cfg.wechat.enabled}
          onChange={(e) => setCfg({ ...cfg, wechat: { ...cfg.wechat, enabled: e.target.checked } })}
          style={{ width: 16, height: 16, cursor: 'pointer' }} />
        启用微信支付
      </label>
      <div style={{ display: 'grid', gap: 10, marginBottom: 20 }}>
        {wcField('AppID', 'appid')}
        {wcField('MchID（商户号）', 'mchid')}
        {wcField('Cert Serial No', 'cert_serial_no')}
        {wcField('APIv3 Key', 'apiv3_key', 'password')}
        {wcField('Private Key（PEM 内容）', 'private_key', 'password')}
        {wcField('回调通知 URL', 'notify_url')}
      </div>

      <h4 style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 8 }}>支付宝</h4>
      <div style={{ display: 'flex', gap: 20, marginBottom: 12 }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, cursor: 'pointer' }}>
          <input type="checkbox" checked={cfg.alipay.enabled}
            onChange={(e) => setCfg({ ...cfg, alipay: { ...cfg.alipay, enabled: e.target.checked } })}
            style={{ width: 16, height: 16, cursor: 'pointer' }} />
          启用支付宝
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, cursor: 'pointer' }}>
          <input type="checkbox" checked={cfg.alipay.sandbox || false}
            onChange={(e) => setCfg({ ...cfg, alipay: { ...cfg.alipay, sandbox: e.target.checked } })}
            style={{ width: 16, height: 16, cursor: 'pointer' }} />
          沙箱模式（测试用）
        </label>
      </div>
      <div style={{ display: 'grid', gap: 10, marginBottom: 16 }}>
        {apField('App ID', 'app_id')}
        {apField('应用私钥（RSA2）', 'private_key', 'password')}
        {apField('支付宝公钥', 'alipay_public_key', 'password')}
        {apField('回调通知 URL', 'notify_url')}
        {apField('同步跳转 URL', 'return_url')}
      </div>

      <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
        {saving ? <RefreshCw size={14} /> : <Save size={14} />}
        {saving ? '保存中...' : '保存支付配置'}
      </button>
    </div>
  );
}

// ─── 短信配置 ────────────────────────────────────────────────
function SmsConfigSection() {
  const defaultCfg = {
    enabled: false, require_phone_on_register: false, provider: 'aliyun',
    aliyun: { access_key_id: '', access_key_secret: '', sign_name: '', template_code: '' },
    tencent: { secret_id: '', secret_key: '', app_id: '', sign_name: '', template_id: '' },
  };
  const [cfg, setCfg] = useState(defaultCfg);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    settingsAPI.getSms().then((res) => setCfg({ ...defaultCfg, ...res.data })).catch(() => {});
  }, []);

  const set = (patch) => setCfg((c) => ({ ...c, ...patch }));
  const setAl = (patch) => setCfg((c) => ({ ...c, aliyun: { ...c.aliyun, ...patch } }));
  const setTc = (patch) => setCfg((c) => ({ ...c, tencent: { ...c.tencent, ...patch } }));

  const handleSave = async () => {
    setSaving(true);
    try {
      await settingsAPI.updateSms(cfg);
      toast.success('短信配置已保存');
    } catch { toast.error('保存失败'); }
    finally { setSaving(false); }
  };

  return (
    <div className="card" style={{ marginBottom: 24 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <h3 style={{ fontSize: 16, margin: 0 }}>短信验证（注册 & 登录）</h3>
        <span style={{ fontSize: 12, padding: '2px 10px', borderRadius: 12, background: cfg.enabled ? '#dcfce7' : '#f3f4f6', color: cfg.enabled ? '#166534' : '#6b7280' }}>
          {cfg.enabled ? '已启用' : '未启用'}
        </span>
      </div>

      <div style={{ display: 'grid', gap: 12 }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 14 }}>
          <input type="checkbox" checked={cfg.enabled} onChange={(e) => set({ enabled: e.target.checked })} style={{ width: 16, height: 16 }} />
          启用短信验证
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 14 }}>
          <input type="checkbox" checked={cfg.require_phone_on_register} onChange={(e) => set({ require_phone_on_register: e.target.checked })} style={{ width: 16, height: 16 }} />
          注册时强制填写手机号并验证
        </label>

        <div>
          <label style={{ display: 'block', marginBottom: 6, fontSize: 13, color: 'var(--text-secondary)' }}>短信服务商</label>
          <select value={cfg.provider} onChange={(e) => set({ provider: e.target.value })}
            style={{ ...inputStyle, padding: '8px 12px' }}>
            <option value="aliyun">阿里云短信</option>
            <option value="tencent">腾讯云短信</option>
          </select>
        </div>

        {cfg.provider === 'aliyun' && (
          <>
            <div>
              <label style={{ display: 'block', marginBottom: 4, fontSize: 13, color: 'var(--text-secondary)' }}>Access Key ID</label>
              <input type="password" value={cfg.aliyun.access_key_id} placeholder="已设置则留空" style={inputStyle}
                onChange={(e) => setAl({ access_key_id: e.target.value })} />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: 4, fontSize: 13, color: 'var(--text-secondary)' }}>Access Key Secret</label>
              <input type="password" value={cfg.aliyun.access_key_secret} placeholder="已设置则留空" style={inputStyle}
                onChange={(e) => setAl({ access_key_secret: e.target.value })} />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: 4, fontSize: 13, color: 'var(--text-secondary)' }}>短信签名</label>
              <input type="text" value={cfg.aliyun.sign_name} placeholder="如：RAG知识库" style={inputStyle}
                onChange={(e) => setAl({ sign_name: e.target.value })} />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: 4, fontSize: 13, color: 'var(--text-secondary)' }}>模板 Code</label>
              <input type="text" value={cfg.aliyun.template_code} placeholder="如：SMS_123456789" style={inputStyle}
                onChange={(e) => setAl({ template_code: e.target.value })} />
            </div>
          </>
        )}

        {cfg.provider === 'tencent' && (
          <>
            <div>
              <label style={{ display: 'block', marginBottom: 4, fontSize: 13, color: 'var(--text-secondary)' }}>Secret ID</label>
              <input type="password" value={cfg.tencent.secret_id} placeholder="已设置则留空" style={inputStyle}
                onChange={(e) => setTc({ secret_id: e.target.value })} />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: 4, fontSize: 13, color: 'var(--text-secondary)' }}>Secret Key</label>
              <input type="password" value={cfg.tencent.secret_key} placeholder="已设置则留空" style={inputStyle}
                onChange={(e) => setTc({ secret_key: e.target.value })} />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: 4, fontSize: 13, color: 'var(--text-secondary)' }}>App ID（SDKAppID）</label>
              <input type="text" value={cfg.tencent.app_id} placeholder="如：1400000000" style={inputStyle}
                onChange={(e) => setTc({ app_id: e.target.value })} />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: 4, fontSize: 13, color: 'var(--text-secondary)' }}>短信签名</label>
              <input type="text" value={cfg.tencent.sign_name} placeholder="如：RAG知识库" style={inputStyle}
                onChange={(e) => setTc({ sign_name: e.target.value })} />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: 4, fontSize: 13, color: 'var(--text-secondary)' }}>模板 ID</label>
              <input type="text" value={cfg.tencent.template_id} placeholder="如：123456" style={inputStyle}
                onChange={(e) => setTc({ template_id: e.target.value })} />
            </div>
          </>
        )}
      </div>

      <button className="btn btn-primary" onClick={handleSave} disabled={saving} style={{ marginTop: 16 }}>
        {saving ? <RefreshCw size={14} /> : <Save size={14} />}
        {saving ? '保存中...' : '保存'}
      </button>
    </div>
  );
}

// ─── 页面 ─────────────────────────────────────────────────────
export default function SystemPage() {
  return (
    <div>
      <div className="page-header">
        <div>
          <h1>系统配置</h1>
          <p>管理支付渠道、短信验证等系统级功能</p>
        </div>
      </div>
      <div style={{ maxWidth: 640 }}>
        <SmsConfigSection />
        <PaymentConfigSection />
      </div>
    </div>
  );
}
