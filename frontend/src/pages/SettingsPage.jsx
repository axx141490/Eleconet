import { useState, useEffect } from 'react';
import { settingsAPI } from '../services/api';
import { Settings, Save, RefreshCw } from 'lucide-react';
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

export default function SettingsPage() {
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
          <p>配置对话和向量化使用的 AI 模型服务</p>
        </div>
        <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
          {saving ? <RefreshCw size={16} className="spin" /> : <Save size={16} />}
          {saving ? '保存中...' : '保存配置'}
        </button>
      </div>

      <div style={{ maxWidth: 640 }}>
        <ProviderSection
          title="对话模型 (LLM)"
          value={llm}
          onChange={setLlm}
          isEmbedding={false}
        />
        <ProviderSection
          title="向量化模型 (Embedding)"
          value={embedding}
          onChange={setEmbedding}
          isEmbedding={true}
        />

        <div className="card" style={{ background: 'var(--warning-light, #fffbeb)', border: '1px solid var(--warning, #f59e0b)' }}>
          <p style={{ fontSize: 13, color: '#92400e', margin: 0 }}>
            ⚠️ 修改 Embedding 模型后，已有知识库的向量数据与新模型不兼容，需要重新上传文档。
          </p>
        </div>
      </div>
    </div>
  );
}
