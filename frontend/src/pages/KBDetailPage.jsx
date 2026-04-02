import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { kbAPI } from '../services/api';
import { Upload, Trash2, FileText, ArrowLeft, MessageSquare, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';

const FILE_TYPE_COLORS = {
  text: '#6366f1', pdf: '#ef4444', docx: '#3b82f6', xlsx: '#22c55e',
  pptx: '#f59e0b', image: '#ec4899', audio: '#8b5cf6', video: '#06b6d4',
};

const FILE_TYPE_LABELS = {
  text: 'TXT', pdf: 'PDF', docx: 'DOC', xlsx: 'XLS',
  pptx: 'PPT', image: 'IMG', audio: 'AUD', video: 'VID',
};

export default function KBDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [kb, setKB] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [dragging, setDragging] = useState(false);

  useEffect(() => { loadKB(); }, [id]);

  // Auto-refresh pending/processing documents
  useEffect(() => {
    if (!kb) return;
    const hasPending = kb.documents?.some((d) => ['pending', 'processing'].includes(d.status));
    if (!hasPending) return;
    const timer = setInterval(loadKB, 3000);
    return () => clearInterval(timer);
  }, [kb]);

  const loadKB = async () => {
    try {
      const res = await kbAPI.get(id);
      setKB(res.data);
    } catch { toast.error('加载知识库失败'); navigate('/knowledge-base'); }
  };

  const handleUpload = async (files) => {
    if (!files.length) return;
    setUploading(true);
    try {
      await kbAPI.uploadFiles(id, Array.from(files), (progress) => {
        // Could add progress bar here
      });
      toast.success(`${files.length} 个文件上传成功，正在处理...`);
      loadKB();
    } catch (err) {
      toast.error(err.response?.data?.detail || '上传失败');
    } finally { setUploading(false); }
  };

  const handleDelete = async (docId) => {
    if (!confirm('确定要删除该文档？')) return;
    try {
      await kbAPI.deleteDocument(id, docId);
      toast.success('文档已删除');
      loadKB();
    } catch { toast.error('删除失败'); }
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  if (!kb) return <div className="loading-screen"><span className="spinner" /> 加载中...</div>;

  return (
    <div>
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button className="btn btn-secondary btn-sm" onClick={() => navigate('/knowledge-base')}>
            <ArrowLeft size={16} />
          </button>
          <div>
            <h1>{kb.name}</h1>
            <p>{kb.description || '暂无描述'} · {kb.document_count} 文档 · {kb.total_chunks} 向量块</p>
          </div>
        </div>
        <button className="btn btn-primary" onClick={() => navigate(`/chat?kb=${id}`)}>
          <MessageSquare size={18} /> 开始问答
        </button>
      </div>

      {/* Upload Area */}
      <div
        className={`upload-area ${dragging ? 'dragging' : ''}`}
        onClick={() => fileInputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          handleUpload(e.dataTransfer.files);
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          style={{ display: 'none' }}
          onChange={(e) => handleUpload(e.target.files)}
          accept=".txt,.md,.csv,.json,.pdf,.docx,.doc,.xlsx,.xls,.pptx,.ppt,.png,.jpg,.jpeg,.gif,.mp3,.wav,.m4a,.mp4,.avi,.mkv,.mov"
        />
        {uploading ? (
          <><span className="spinner" /> 上传中...</>
        ) : (
          <>
            <Upload size={36} color="var(--primary)" />
            <p>点击或拖拽文件到此区域上传</p>
            <p style={{ fontSize: 12 }}>支持 TXT、PDF、Word、Excel、PPT、图片、音频、视频等格式</p>
          </>
        )}
      </div>

      {/* Document List */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <h2 style={{ fontSize: 18 }}>文档列表 ({kb.documents?.length || 0})</h2>
        <button className="btn btn-secondary btn-sm" onClick={loadKB}>
          <RefreshCw size={14} /> 刷新
        </button>
      </div>

      {kb.documents?.length > 0 ? (
        <div className="doc-list">
          {kb.documents.map((doc) => (
            <div key={doc.id} className="doc-item">
              <div className="doc-info">
                <div className="file-icon" style={{
                  background: (FILE_TYPE_COLORS[doc.file_type] || '#999') + '20',
                  color: FILE_TYPE_COLORS[doc.file_type] || '#999',
                  fontSize: 12,
                }}>
                  {FILE_TYPE_LABELS[doc.file_type] || 'FILE'}
                </div>
                <div>
                  <div style={{ fontWeight: 500, fontSize: 14 }}>{doc.filename}</div>
                  <div className="doc-meta">
                    {formatSize(doc.file_size)} · {doc.chunk_count} 块 · {new Date(doc.created_at).toLocaleString()}
                    {doc.error_message && <span style={{ color: 'var(--danger)' }}> · {doc.error_message}</span>}
                  </div>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span className={`status-badge status-${doc.status}`}>
                  {doc.status === 'completed' ? '已完成' : doc.status === 'processing' ? '处理中' :
                    doc.status === 'pending' ? '等待中' : '失败'}
                </span>
                <button className="btn btn-sm" style={{ color: 'var(--danger)', padding: 4 }}
                  onClick={() => handleDelete(doc.id)}>
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <FileText size={48} />
          <h3>暂无文档</h3>
          <p>上传文件到该知识库开始使用</p>
        </div>
      )}
    </div>
  );
}
