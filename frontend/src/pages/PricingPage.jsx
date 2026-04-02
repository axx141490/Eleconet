import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { paymentAPI } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { Check, X, Zap } from 'lucide-react';
import toast from 'react-hot-toast';

const FEATURES = [
  { key: 'kb', label: '知识库数量', free: '5', pro: '100', enterprise: '100' },
  { key: 'docs', label: '单库文档数', free: '10', pro: '100', enterprise: '1000' },
  { key: 'size', label: '单文件大小', free: '1 MB', pro: '1 GB', enterprise: '1 GB' },
  { key: 'fmt', label: '文件格式', free: '基础(TXT/PDF/Word)', pro: '全部格式', enterprise: '全部格式' },
  { key: 'share', label: '分享链接', free: false, pro: true, enterprise: true },
  { key: 'history', label: '对话历史', free: '10 条', pro: '100 条', enterprise: '1000 条' },
];

const TIER_COLORS = {
  free: { bg: '#f8fafc', border: '#e2e8f0', btn: '#64748b', badge: null },
  pro: { bg: '#eff6ff', border: '#3b82f6', btn: '#2563eb', badge: '最受欢迎' },
  enterprise: { bg: '#faf5ff', border: '#7c3aed', btn: '#7c3aed', badge: '功能最全' },
};

function FeatureCell({ value }) {
  if (value === true) return <Check size={16} color="#22c55e" />;
  if (value === false) return <X size={16} color="#ef4444" />;
  return <span style={{ fontSize: 13 }}>{value}</span>;
}

export default function PricingPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [yearly, setYearly] = useState(false);
  const [plans, setPlans] = useState(null);
  const [methods, setMethods] = useState({ wechat: false, alipay: false });

  useEffect(() => {
    paymentAPI.getPlans().then((res) => {
      const planMap = {};
      res.data.plans.forEach((p) => { planMap[p.tier] = p; });
      setPlans(planMap);
      setMethods({ wechat: res.data.wechat_enabled, alipay: res.data.alipay_enabled });
    }).catch(() => {});
  }, []);

  const fmt = (fen) => fen === 0 ? '免费' : `¥${(fen / 100).toFixed(0)}`;

  const handleUpgrade = (tier, payMethod) => {
    if (!user) { navigate('/login'); return; }
    navigate(`/payment?tier=${tier}&months=${yearly ? 12 : 1}&method=${payMethod}`);
  };

  const tiers = ['free', 'pro', 'enterprise'];
  const noPayment = plans && !methods.wechat && !methods.alipay;

  return (
    <div style={{ minHeight: '100vh', background: '#f8fafc', padding: '40px 24px' }}>
      <div style={{ maxWidth: 960, margin: '0 auto' }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <h1 style={{ fontSize: 32, fontWeight: 700, color: '#1e293b', marginBottom: 8 }}>选择适合你的套餐</h1>
          <p style={{ color: '#64748b', fontSize: 16 }}>按需升级，随时取消</p>

          {/* Monthly/Yearly toggle */}
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 12, marginTop: 20,
            background: '#fff', border: '1px solid #e2e8f0', borderRadius: 24, padding: '6px 16px' }}>
            <button onClick={() => setYearly(false)} style={{
              padding: '4px 16px', borderRadius: 16, border: 'none', cursor: 'pointer', fontSize: 14, fontWeight: 500,
              background: !yearly ? '#2563eb' : 'transparent',
              color: !yearly ? '#fff' : '#64748b',
            }}>按月</button>
            <button onClick={() => setYearly(true)} style={{
              padding: '4px 16px', borderRadius: 16, border: 'none', cursor: 'pointer', fontSize: 14, fontWeight: 500,
              background: yearly ? '#2563eb' : 'transparent',
              color: yearly ? '#fff' : '#64748b',
            }}>按年
              <span style={{ marginLeft: 6, fontSize: 11, background: '#fef9c3', color: '#854d0e',
                padding: '1px 6px', borderRadius: 8, fontWeight: 600 }}>省30%</span>
            </button>
          </div>
        </div>

        {/* Plan Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20, marginBottom: 40 }}>
          {tiers.map((tier) => {
            const colors = TIER_COLORS[tier];
            const plan = plans?.[tier];
            const price = plan ? (yearly ? plan.yearly_fen : plan.monthly_fen) : 0;
            const isCurrent = user?.tier === tier;

            return (
              <div key={tier} style={{
                background: colors.bg, border: `2px solid ${isCurrent ? colors.btn : colors.border}`,
                borderRadius: 16, padding: 28, position: 'relative', display: 'flex', flexDirection: 'column',
              }}>
                {colors.badge && (
                  <div style={{ position: 'absolute', top: -12, left: '50%', transform: 'translateX(-50%)',
                    background: colors.btn, color: '#fff', fontSize: 11, fontWeight: 700,
                    padding: '3px 12px', borderRadius: 12 }}>
                    {colors.badge}
                  </div>
                )}
                {isCurrent && (
                  <div style={{ position: 'absolute', top: -12, right: 16,
                    background: '#22c55e', color: '#fff', fontSize: 11, fontWeight: 700,
                    padding: '3px 12px', borderRadius: 12 }}>当前套餐</div>
                )}

                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 20, fontWeight: 700, color: '#1e293b', marginBottom: 4 }}>
                    {tier === 'free' ? 'Free' : tier === 'pro' ? 'Pro' : 'Enterprise'}
                  </div>
                  <div style={{ fontSize: 32, fontWeight: 800, color: colors.btn }}>
                    {price === 0 ? '免费' : `¥${(price / 100).toFixed(0)}`}
                    {price > 0 && <span style={{ fontSize: 14, fontWeight: 400, color: '#64748b' }}>
                      /{yearly ? '年' : '月'}
                    </span>}
                  </div>
                  {yearly && price > 0 && plan && (
                    <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 2 }}>
                      相当于 ¥{((price / 100) / 12).toFixed(0)}/月
                    </div>
                  )}
                </div>

                <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 20px', flex: 1 }}>
                  {FEATURES.map((f) => (
                    <li key={f.key} style={{ display: 'flex', alignItems: 'center', gap: 8,
                      padding: '6px 0', fontSize: 13, color: '#374151' }}>
                      {f[tier] === false
                        ? <X size={14} color="#d1d5db" />
                        : <Check size={14} color={colors.btn} />}
                      <span>{f.label}：</span>
                      <span style={{ fontWeight: 500 }}>
                        {f[tier] === true ? '支持' : f[tier] === false ? '不支持' : f[tier]}
                      </span>
                    </li>
                  ))}
                </ul>

                {tier === 'free' ? (
                  <button disabled style={{
                    padding: '10px 0', borderRadius: 8, border: '1px solid #e2e8f0',
                    background: '#f1f5f9', color: '#94a3b8', fontSize: 14, cursor: 'default',
                  }}>
                    {isCurrent ? '当前使用中' : '免费开始'}
                  </button>
                ) : isCurrent ? (
                  <button disabled style={{
                    padding: '10px 0', borderRadius: 8, border: 'none',
                    background: '#dcfce7', color: '#166534', fontSize: 14, cursor: 'default', fontWeight: 600,
                  }}>✓ 已订阅</button>
                ) : noPayment ? (
                  <button disabled style={{
                    padding: '10px 0', borderRadius: 8, border: 'none',
                    background: '#f1f5f9', color: '#94a3b8', fontSize: 14, cursor: 'default',
                  }}>暂未开放购买</button>
                ) : (
                  <div style={{ display: 'flex', gap: 8 }}>
                    {methods.wechat && (
                      <button onClick={() => handleUpgrade(tier, 'wechat')} style={{
                        flex: 1, padding: '10px 0', borderRadius: 8, border: 'none',
                        background: '#07c160', color: '#fff', fontSize: 13, cursor: 'pointer', fontWeight: 600,
                      }}>微信支付</button>
                    )}
                    {methods.alipay && (
                      <button onClick={() => handleUpgrade(tier, 'alipay')} style={{
                        flex: 1, padding: '10px 0', borderRadius: 8, border: 'none',
                        background: '#1677ff', color: '#fff', fontSize: 13, cursor: 'pointer', fontWeight: 600,
                      }}>支付宝</button>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Feature comparison table */}
        <div style={{ background: '#fff', borderRadius: 16, border: '1px solid #e2e8f0', overflow: 'hidden' }}>
          <div style={{ padding: '20px 24px', borderBottom: '1px solid #f1f5f9' }}>
            <h2 style={{ fontSize: 18, fontWeight: 600, margin: 0 }}>功能对比</h2>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
            <thead>
              <tr style={{ background: '#f8fafc' }}>
                <th style={{ padding: '12px 24px', textAlign: 'left', color: '#64748b', fontWeight: 600 }}>功能</th>
                {['Free', 'Pro', 'Enterprise'].map((n) => (
                  <th key={n} style={{ padding: '12px 16px', textAlign: 'center', color: '#64748b', fontWeight: 600 }}>{n}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {FEATURES.map((f, i) => (
                <tr key={f.key} style={{ borderTop: '1px solid #f1f5f9', background: i % 2 === 0 ? '#fff' : '#fafafa' }}>
                  <td style={{ padding: '12px 24px', color: '#374151' }}>{f.label}</td>
                  {['free', 'pro', 'enterprise'].map((t) => (
                    <td key={t} style={{ padding: '12px 16px', textAlign: 'center' }}>
                      <FeatureCell value={f[t]} />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p style={{ textAlign: 'center', color: '#94a3b8', fontSize: 13, marginTop: 24 }}>
          有问题？联系我们的支持团队
        </p>
      </div>
    </div>
  );
}
