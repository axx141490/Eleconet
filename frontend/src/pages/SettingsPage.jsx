import { useState, useEffect } from 'react';
import { settingsAPI, paymentAPI } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { Save, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';

const PROVIDERS = [
  { value: 'openai',   label: 'OpenAI' },
  { value: 'deepseek', label: 'DeepSeek' },
  { value: 'zhipu',    label: '智谱 AI (GLM)' },
  { value: 'qwen',     label: '通义千问 (Qwen)' },
  { value: 'ollama',   label: 'Ollama (本地)' },
  { value: 'custom',   label: '自定义 (兼容 OpenAI)' },
];

const PRESETS = {
  openai:   { base_url: 'https://api.openai.com/v1',                   chat_model: 'gpt-4o-mini',      embedding_model: 'text-embedding-3-small' },
  deepseek: { base_url: 'https://api.deepseek.com/v1',                  chat_model: 'deepseek-chat',    embedding_model: '' },
  zhipu:    { base_url: 'https://open.bigmodel.cn/api/paas/v4/',        chat_model: 'glm-4-flash',      embedding_model: 'embedding-3' },
  qwen:     { base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1', chat_model: 'qwen-plus',    embedding_model: 'text-embedding-v3' },
  ollama:   { base_url: 'http://host.docker.internal:11434/v1',         chat_model: 'qwen2.5:7b',       embedding_model: 'nomic-embed-text' },
  custom:   { base_url: '',                                              chat_model: '',                 embedding_model: '' },
};

function ProviderSection({ title, value, onChange, isEmbedding }) {
  const preset = PRESETS[value.provider] || PRESETS.custom;

  const applyPreset = (provider) => {
    const p = PRESETS[provider] || PRESETS.custom;
    onChange({
      ...value,
      provider,
      base_url: p.base_url,
      model: isEmbedding ? p.embedding_model : p.chat_model,
    });
  };

  return (
    <div className="card" style={{ marginBottom: 24 }}>
      <h3 style={{ marginBottom: 16, fontSize: 16 }}>{title}</h3>

      <div style={{ display: 'grid', gap: 16 }}>
        <div>
          <label style={{ display: 'block', marginBottom: 6, fontSize: 13, color: 'var(--text-secondary)' }}>服务商</label>
          <select
            className="form-select"
            value={value.provider}
            onChange={(e) => applyPreset(e.target.value)}
            style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border)', fontSize: 14 }}
          >
            {PROVIDERS.map((p) => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: 6, fontSize: 13, color: 'var(--text-secondary)' }}>
            API Key {value.provider === 'ollama' ? '（本地无需填写）' : ''}
          </label>
          <input
            type="password"
            className="form-input"
            placeholder={value.provider === 'ollama' ? '无需填写' : '输入 API Key'}
            value={value.api_key || ''}
            onChange={(e) => onChange({ ...value, api_key: e.target.value })}
            disabled={value.provider === 'ollama'}
            style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border)', fontSize: 14, boxSizing: 'border-box' }}
          />
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: 6, fontSize: 13, color: 'var(--text-secondary)' }}>
            Base URL <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>（留空使用默认值）</span>
          </label>
          <input
            type="text"
            className="form-input"
            placeholder={preset.base_url || '例: https://api.example.com/v1'}
            value={value.base_url || ''}
            onChange={(e) => onChange({ ...value, base_url: e.target.value })}
            style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border)', fontSize: 14, boxSizing: 'border-box' }}
          />
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: 6, fontSize: 13, color: 'var(--text-secondary)' }}>模型名称</label>
          <input
            type="text"
            className="form-input"
            placeholder={isEmbedding ? preset.embedding_model || '例: text-embedding-3-small' : preset.chat_model || '例: gpt-4o-mini'}
            value={value.model || ''}
            onChange={(e) => onChange({ ...value, model: e.target.value })}
            style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border)', fontSize: 14, boxSizing: 'border-box' }}
          />
        </div>
      </div>
    </div>
  );
}

const inputStyle = { width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border)', fontSize: 14, boxSizing: 'border-box' };

function BaiduOCRSection() {
  const [cfg, setCfg] = useState({ api_key: '', secret_key: '', enabled: false });
  const [enabled, setEnabled] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    settingsAPI.getBaiduOCR().then((res) => {
      setCfg({ api_key: res.data.api_key, secret_key: res.data.secret_key, enabled: res.data.enabled });
      setEnabled(res.data.enabled);
    }).catch(() => {});
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await settingsAPI.updateBaiduOCR(cfg);
      toast.success('百度 OCR 配置已保存');
      setEnabled(cfg.enabled);
    } catch { toast.error('保存失败'); }
    finally { setSaving(false); }
  };

  return (
    <div className="card" style={{ marginBottom: 24 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <h3 style={{ fontSize: 16, margin: 0 }}>百度 OCR（扫描版 PDF）</h3>
        <span style={{ fontSize: 12, padding: '2px 10px', borderRadius: 12, background: enabled ? '#dcfce7' : '#f3f4f6', color: enabled ? '#166534' : '#6b7280' }}>
          {enabled ? '已启用' : '未配置'}
        </span>
      </div>
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
        配置后，扫描版 PDF 将优先使用百度 OCR 识别，准确率高于本地 Tesseract。
      </p>
      <div style={{ display: 'grid', gap: 12 }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 14 }}>
          <input
            type="checkbox"
            checked={cfg.enabled}
            onChange={(e) => setCfg({ ...cfg, enabled: e.target.checked })}
            style={{ width: 16, height: 16, cursor: 'pointer' }}
          />
          启用百度 OCR
        </label>
        <div>
          <label style={{ display: 'block', marginBottom: 6, fontSize: 13, color: 'var(--text-secondary)' }}>API Key</label>
          <input type="password" placeholder="输入百度 OCR API Key" value={cfg.api_key}
            onChange={(e) => setCfg({ ...cfg, api_key: e.target.value })} style={inputStyle} />
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: 6, fontSize: 13, color: 'var(--text-secondary)' }}>Secret Key</label>
          <input type="password" placeholder="输入百度 OCR Secret Key" value={cfg.secret_key}
            onChange={(e) => setCfg({ ...cfg, secret_key: e.target.value })} style={inputStyle} />
        </div>
      </div>
      <button className="btn btn-primary" onClick={handleSave} disabled={saving} style={{ marginTop: 16 }}>
        {saving ? <RefreshCw size={14} /> : <Save size={14} />}
        {saving ? '保存中...' : '保存'}
      </button>
    </div>
  );
}

function PaymentConfigSection() {
  const inputStyle2 = { width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border)', fontSize: 13, boxSizing: 'border-box' };
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
      <input type="number" value={cfg.pricing[key] || 0} style={inputStyle2}
        onChange={(e) => setCfg({ ...cfg, pricing: { ...cfg.pricing, [key]: parseInt(e.target.value) } })} />
    </div>
  );

  const wcField = (label, key, type = 'text') => (
    <div>
      <label style={{ display: 'block', marginBottom: 4, fontSize: 12, color: 'var(--text-secondary)' }}>{label}</label>
      <input type={type} value={cfg.wechat[key] || ''} placeholder={key.includes('key') ? '已设置则留空' : ''} style={inputStyle2}
        onChange={(e) => setCfg({ ...cfg, wechat: { ...cfg.wechat, [key]: e.target.value } })} />
    </div>
  );

  const apField = (label, key, type = 'text') => (
    <div>
      <label style={{ display: 'block', marginBottom: 4, fontSize: 12, color: 'var(--text-secondary)' }}>{label}</label>
      <input type={type} value={cfg.alipay[key] || ''} placeholder={key.includes('key') ? '已设置则留空' : ''} style={inputStyle2}
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

export default function SettingsPage() {
  const { user } = useAuth();
  const [llm, setLlm] = useState({ provider: 'openai', api_key: '', base_url: '', model: 'gpt-4o-mini' });
  const [embedding, setEmbedding] = useState({ provider: 'openai', api_key: '', base_url: '', model: 'text-embedding-3-small' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => { loadConfig(); }, []);

  const loadConfig = async () => {
    try {
      const res = await settingsAPI.getModel();
      setLlm(res.data.llm);
      setEmbedding(res.data.embedding);
    } catch {
      toast.error('加载配置失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await settingsAPI.updateModel({ llm, embedding });
      toast.success('配置已保存');
    } catch {
      toast.error('保存失败');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div style={{ padding: 32 }}>加载中...</div>;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>模型配置</h1>
          <p>配置对话、向量化和 OCR 使用的 AI 服务</p>
        </div>
        <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
          {saving ? <RefreshCw size={16} className="spin" /> : <Save size={16} />}
          {saving ? '保存中...' : '保存配置'}
        </button>
      </div>

      <div style={{ maxWidth: 640 }}>
        <ProviderSection title="对话模型 (LLM)" value={llm} onChange={setLlm} isEmbedding={false} />
        <ProviderSection title="向量化模型 (Embedding)" value={embedding} onChange={setEmbedding} isEmbedding={true} />
        <BaiduOCRSection />
        {user?.is_admin && <PaymentConfigSection />}
        <div className="card" style={{ background: 'var(--warning-light, #fffbeb)', border: '1px solid var(--warning, #f59e0b)' }}>
          <p style={{ fontSize: 13, color: '#92400e', margin: 0 }}>
            ⚠️ 修改 Embedding 模型后，已有知识库的向量数据与新模型不兼容，需要重新上传文档。
          </p>
        </div>
      </div>
    </div>
  );
}
