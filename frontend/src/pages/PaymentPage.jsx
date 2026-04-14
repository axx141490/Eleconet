import { useState, useEffect, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { paymentAPI } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { CheckCircle, Loader, RefreshCw, ArrowLeft } from 'lucide-react';
import toast from 'react-hot-toast';

const TIER_NAMES = { pro: 'Pro', enterprise: 'Enterprise' };
const METHOD_NAMES = { wechat: '微信支付', alipay: '支付宝' };
const METHOD_COLORS = { wechat: '#07c160', alipay: '#1677ff' };

// Pricing mirror (fen) — used for display before order is created
const PRICE_TABLE = {
  pro_1: 2900, pro_12: 19900,
  enterprise_1: 9900, enterprise_12: 69900,
};

export default function PaymentPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user, refreshUser } = useAuth();

  const tier = searchParams.get('tier') || 'pro';
  const months = parseInt(searchParams.get('months') || '1', 10);
  const method = searchParams.get('method') || 'wechat';

  const [order, setOrder] = useState(null);
  const [status, setStatus] = useState('creating'); // creating / pending / paid / error
  const [error, setError] = useState('');
  const [sandbox, setSandbox] = useState(false);
  const pollRef = useRef(null);

  useEffect(() => {
    createOrder();
    return () => clearInterval(pollRef.current);
  }, []);

  const createOrder = async () => {
    setStatus('creating');
    try {
      const [plansRes, orderRes] = await Promise.all([
        paymentAPI.getPlans(),
        paymentAPI.createOrder({ tier, duration_months: months, pay_method: method }),
      ]);
      setSandbox(plansRes.data?.alipay_sandbox || false);
      orderNoRef.current = orderRes.data.order_no;
      setOrder(orderRes.data);

      // 支付宝电脑网站支付：直接跳转
      if (method === 'alipay' && orderRes.data.qr_code_url) {
        window.location.href = orderRes.data.qr_code_url;
        return;
      }

      setStatus('pending');
      pollRef.current = setInterval(pollStatus, 3000);
    } catch (err) {
      setError(err.response?.data?.detail || '创建订单失败');
      setStatus('error');
    }
  };

  const orderNoRef = useRef('');
  const pollStatus = async () => {
    if (!orderNoRef.current) return;
    try {
      const res = await paymentAPI.getOrder(orderNoRef.current);
      if (res.data.status === 'paid') {
        clearInterval(pollRef.current);
        setStatus('paid');
        if (refreshUser) await refreshUser();
      }
    } catch {}
  };

  const handleSimulatePay = async () => {
    if (!order) return;
    try {
      await paymentAPI.simulatePay(order.order_no);
      clearInterval(pollRef.current);
      setStatus('paid');
      if (refreshUser) await refreshUser();
    } catch (err) {
      toast.error(err.response?.data?.detail || '模拟支付失败');
    }
  };

  // Manual refresh
  const handleCheckPaid = async () => {
    if (!order) return;
    try {
      const res = await paymentAPI.getOrder(order.order_no);
      if (res.data.status === 'paid') {
        clearInterval(pollRef.current);
        setStatus('paid');
        if (refreshUser) await refreshUser();
      } else {
        toast('尚未检测到支付，请稍后再试');
      }
    } catch {
      toast.error('查询失败');
    }
  };

  const estimatedFen = PRICE_TABLE[`${tier}_${months}`] || 0;
  const amountYuan = order
    ? (order.amount_fen / 100).toFixed(2)
    : estimatedFen > 0 ? (estimatedFen / 100).toFixed(2) : '--';
  const qrUrl = order?.qr_code_url
    ? `https://quickchart.io/qr?text=${encodeURIComponent(order.qr_code_url)}&size=240`
    : null;

  if (status === 'paid') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        minHeight: '80vh', gap: 16 }}>
        <CheckCircle size={72} color="#22c55e" />
        <h2 style={{ fontSize: 24, fontWeight: 700, color: '#1e293b' }}>支付成功！</h2>
        <p style={{ color: '#64748b' }}>
          你的账号已升级为 <strong>{TIER_NAMES[tier]}</strong> 套餐（{months === 12 ? '12个月' : '1个月'}）
        </p>
        <button className="btn btn-primary" onClick={() => navigate('/')}>
          开始使用
        </button>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 480, margin: '40px auto', padding: '0 24px' }}>
      <button className="btn btn-secondary btn-sm" onClick={() => navigate('/pricing')}
        style={{ marginBottom: 24 }}>
        <ArrowLeft size={14} /> 返回套餐选择
      </button>

      <div style={{ background: '#fff', borderRadius: 16, border: '1px solid #e2e8f0', padding: 32 }}>
        <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 4 }}>确认支付</h2>
        <p style={{ color: '#64748b', marginBottom: 24, fontSize: 14 }}>
          {TIER_NAMES[tier]} 套餐 · {months === 12 ? '12个月（年付）' : '1个月（月付）'}
        </p>

        {/* Order summary */}
        <div style={{ background: '#f8fafc', borderRadius: 10, padding: 16, marginBottom: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
            <span style={{ color: '#64748b', fontSize: 14 }}>套餐</span>
            <span style={{ fontWeight: 600 }}>{TIER_NAMES[tier]}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
            <span style={{ color: '#64748b', fontSize: 14 }}>时长</span>
            <span style={{ fontWeight: 600 }}>{months === 12 ? '12个月' : '1个月'}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: 8, borderTop: '1px solid #e2e8f0' }}>
            <span style={{ color: '#64748b', fontSize: 14 }}>应付金额</span>
            <span style={{ fontWeight: 800, fontSize: 20, color: METHOD_COLORS[method] }}>¥{amountYuan}</span>
          </div>
        </div>

        {/* QR / Loading */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
          {status === 'creating' && (
            <>
              <Loader size={36} className="spin" color="#6366f1" />
              <p style={{ color: '#64748b', fontSize: 14 }}>正在生成支付码...</p>
            </>
          )}

          {status === 'pending' && qrUrl && (
            <>
              <div style={{ padding: 8, border: `3px solid ${METHOD_COLORS[method]}`, borderRadius: 12 }}>
                <img src={qrUrl} width={240} height={240} alt="支付二维码"
                  style={{ display: 'block', borderRadius: 8 }} />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{ width: 10, height: 10, borderRadius: '50%', background: METHOD_COLORS[method],
                  animation: 'pulse 1.5s infinite' }} />
                <span style={{ fontSize: 14, color: '#374151' }}>
                  请用<strong style={{ color: METHOD_COLORS[method] }}>{METHOD_NAMES[method]}</strong>扫码支付
                </span>
              </div>
              <p style={{ fontSize: 12, color: '#94a3b8', textAlign: 'center', margin: 0 }}>
                二维码有效期15分钟，支付后自动跳转
              </p>
              <button className="btn btn-secondary btn-sm" onClick={handleCheckPaid}>
                <RefreshCw size={13} /> 我已支付，刷新状态
              </button>
              {sandbox && (
                <button onClick={handleSimulatePay} style={{
                  marginTop: 4, padding: '8px 20px', borderRadius: 8, border: '1px dashed #f59e0b',
                  background: '#fffbeb', color: '#b45309', fontSize: 13, cursor: 'pointer', fontWeight: 600,
                }}>
                  🧪 沙箱模式：模拟支付成功
                </button>
              )}
            </>
          )}

          {status === 'error' && (
            <>
              <p style={{ color: '#ef4444', textAlign: 'center' }}>{error}</p>
              <button className="btn btn-primary btn-sm" onClick={createOrder}>重试</button>
            </>
          )}
        </div>

        {order && (
          <p style={{ fontSize: 11, color: '#cbd5e1', textAlign: 'center', marginTop: 20 }}>
            订单号：{order.order_no}
          </p>
        )}
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
