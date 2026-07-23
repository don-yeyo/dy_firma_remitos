import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

// Interceptor global: agrega el header de ngrok y la clave de autenticación X-API-Key
axios.interceptors.request.use((config) => {
  config.headers['ngrok-skip-browser-warning'] = 'true';
  const apiKey = import.meta.env.VITE_API_SECRET_KEY || 'dy_secret_remitos_2026_default_key';
  if (apiKey) {
    config.headers['X-API-Key'] = apiKey;
  }
  return config;
});
import { useAuth } from './config/AuthContext';
import packageJson from '../package.json';
import {
  Play,
  Cpu,
  RefreshCw,
  Printer,
  LogOut,
  Settings,
  CheckCircle,
  XCircle,
  Loader,
  Clock,
  Sun,
  Moon,
  Search,
  ChevronLeft,
  ChevronRight,
  Mail,
  Check,
  Edit,
  Eye
} from 'lucide-react';

const appVersion = packageJson.version || '1.0.0';

function App() {
  const { isAuthenticated, user, loginMicrosoft, logout } = useAuth();

  // URL de la API local
  const [apiUrl, setApiUrl] = useState(() => {
    return localStorage.getItem('dy_remitos_api_url') || import.meta.env.VITE_API_URL || 'http://localhost:8000';
  });
  const [isConfigOpen, setIsConfigOpen] = useState(false);
  const [tempApiUrl, setTempApiUrl] = useState(apiUrl);

  // Tema claro/oscuro
  const [isDark, setIsDark] = useState(() => {
    return localStorage.getItem('dy_theme') === 'dark' || !localStorage.getItem('dy_theme');
  });

  useEffect(() => {
    if (isDark) {
      document.body.classList.add('dark-theme');
      localStorage.setItem('dy_theme', 'dark');
    } else {
      document.body.classList.remove('dark-theme');
      localStorage.setItem('dy_theme', 'light');
    }
  }, [isDark]);

  // Estados del Dashboard e Historial
  const [activeTab, setActiveTab] = useState('actions'); // 'actions' o 'history'
  const [status, setStatus] = useState('idle');
  const [progress, setProgress] = useState({ message: '', current: 0, total: 0 });
  const [history, setHistory] = useState([]);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);

  // Paginación y búsqueda
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortField, setSortField] = useState('transaccion_id');
  const [sortDir, setSortDir] = useState('desc');

  // Reclamos
  const [selectedIds, setSelectedIds] = useState([]);
  const [isReclamando, setIsReclamando] = useState(false);

  // Estados de control de modales
  const [showModal, setShowModal] = useState(false); // Modal de progreso
  const [actionStarted, setActionStarted] = useState(false); // Indica si iniciamos un proceso
  const [summaryData, setSummaryData] = useState(null); // Estadísticas del modal final
  const [showCancelConfirm, setShowCancelConfirm] = useState(false); // Confirmar cancelación premium
  const [cancelRequested, setCancelRequested] = useState(false); // Bandera de estado en cancelación

  // Dashboard & Estadísticas
  const [dashboardStats, setDashboardStats] = useState(null);
  const [isStatsLoading, setIsStatsLoading] = useState(false);

  // Modales de acciones del historial
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingRemito, setEditingRemito] = useState(null);
  const [showViewerModal, setShowViewerModal] = useState(false);
  const [viewingRemito, setViewingRemito] = useState(null);
  const [zoomLevel, setZoomLevel] = useState(1.0);
  const [emailDestinatarios, setEmailDestinatarios] = useState('');
  const [isSendingEmail, setIsSendingEmail] = useState(false);
  const [showSyncConfirmModal, setShowSyncConfirmModal] = useState(false);

  // Modales de reclamos interactivos
  const [showReclaimModal, setShowReclaimModal] = useState(false);
  const [reclaimDraft, setReclaimDraft] = useState(null);
  const [isPreparingReclaim, setIsPreparingReclaim] = useState(false);
  const [isSendingReclaim, setIsSendingReclaim] = useState(false);
  const [activeReclaimTab, setActiveReclaimTab] = useState('preview'); // 'editor' | 'preview'
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (mobile) {
        setActiveTab('actions');
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const saveApiConfig = (e) => {
    e.preventDefault();
    const formattedUrl = tempApiUrl.replace(/\/$/, '');
    setApiUrl(formattedUrl);
    localStorage.setItem('dy_remitos_api_url', formattedUrl);
    setIsConfigOpen(false);
  };

  // Bloquear scroll en body cuando está abierto cualquier modal activo
  useEffect(() => {
    const anyModalOpen = showModal || showCancelConfirm || isConfigOpen || showEditModal || showSyncConfirmModal;
    if (anyModalOpen) {
      document.body.classList.add('modal-open');
    } else {
      document.body.classList.remove('modal-open');
    }
    return () => {
      document.body.classList.remove('modal-open');
    };
  }, [showModal, showCancelConfirm, isConfigOpen, showEditModal, showSyncConfirmModal]);

  // Polling dinámico: solo consulta /api/status si hay un proceso corriendo
  useEffect(() => {
    if (!isAuthenticated) return;
    if (status === 'idle') return;

    let isMounted = true;

    const fetchStatus = async () => {
      try {
        const res = await axios.get(`${apiUrl}/api/status`);
        if (!isMounted) return;

        setStatus(res.data.status);
        setCancelRequested(res.data.cancel_requested || false);
        setProgress({
          message: res.data.progress_message || '',
          current: res.data.current_step || 0,
          total: res.data.total_steps || 0
        });

        if (res.data.status === 'idle') {
          setCancelRequested(false);
          // El servidor finalizó el trabajo
          if (res.data.last_result) {
            setSummaryData(res.data.last_result);
          } else if (actionStarted) {
            // Si el frontend disparó una acción y esta finalizó, forzamos un resumen genérico de confirmación
            setSummaryData({
              success: true,
              cancelled: false,
              type: status,
              message: "Proceso completado. Los datos han sido guardados.",
              summary: {
                escaneados: 0,
                exitosasIa: 0,
                fallidosIa: 0,
                bdActualizados: 0,
                bdNoEncontrados: 0
              }
            });
          } else {
            // Si el servidor pasó a reposo pero no hay resultados ni acción disparada, cerramos el modal
            setShowModal(false);
            setActionStarted(false);
          }
          fetchHistory(currentPage); // Recargar historial automáticamente
        }
      } catch (err) {
        // Enlace temporalmente offline
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [isAuthenticated, apiUrl, status]);

  // Cargar Historial paginado
  // Cargar Historial paginado
  const fetchHistory = async (page = 1, search = searchQuery, field = sortField, dir = sortDir) => {
    if (!isAuthenticated) return;
    setIsHistoryLoading(true);
    try {
      const res = await axios.get(`${apiUrl}/api/history`, {
        params: {
          page,
          limit: 12,
          search: search.trim() || undefined,
          sort_field: field || undefined,
          sort_dir: dir || undefined
        }
      });
      if (res.data && Array.isArray(res.data.items)) {
        setHistory(res.data.items);
        setTotalPages(res.data.pages || 1);
        setCurrentPage(res.data.page || 1);
        setTotalItems(res.data.total || 0);
      }
    } catch (err) {
      console.error("Error al traer historial:", err);
    } finally {
      setIsHistoryLoading(false);
    }
  };

  const handleSort = (field) => {
    let newDir = 'asc';
    if (sortField === field) {
      newDir = sortDir === 'asc' ? 'desc' : 'asc';
    }
    setSortField(field);
    setSortDir(newDir);
    fetchHistory(currentPage, searchQuery, field, newDir);
  };

  const renderSortIcon = (field) => {
    if (sortField !== field) return <span style={{ opacity: 0.3, marginLeft: 6, fontSize: '11px' }}>↕</span>;
    return sortDir === 'asc' ?
      <span style={{ color: 'var(--primary)', marginLeft: 6, fontWeight: 800, fontSize: '11px' }}>▲</span> :
      <span style={{ color: 'var(--primary)', marginLeft: 6, fontWeight: 800, fontSize: '11px' }}>▼</span>;
  };

  const fetchStats = async () => {
    setIsStatsLoading(true);
    try {
      const res = await axios.get(`${apiUrl}/api/stats`);
      if (res.data.status === 'success') {
        setDashboardStats(res.data.metrics);
      }
    } catch (err) {
      console.error("Error al obtener estadísticas:", err);
    } finally {
      setIsStatsLoading(false);
    }
  };

  const handleSaveEdit = async (e) => {
    e.preventDefault();
    if (!editingRemito) return;
    try {
      const res = await axios.put(`${apiUrl}/api/history/${editingRemito.finne_transaccionID}`, {
        confirmado_cliente: editingRemito.bot_confirmado_cliente === 1 || editingRemito.bot_confirmado_cliente === true,
        confirmado_distribuidor: editingRemito.bot_confirmado_distribuidor === 1 || editingRemito.bot_confirmado_distribuidor === true,
        reclamado: editingRemito.finne_Reclamado === 1 || editingRemito.finne_Reclamado === true,
        fecha_ultimo_reclamo: editingRemito.finne_FechaUltimoReclamo,
        copias_presentes: {
          original: !!editingRemito.ocr_original,
          duplicado: !!editingRemito.ocr_duplicado,
          triplicado: !!editingRemito.ocr_triplicado,
          cuatriplicado: !!editingRemito.ocr_cuatriplcado
        }
      });
      if (res.data.status === 'success') {
        setShowEditModal(false);
        fetchHistory(currentPage);
        alert("Remito guardado con éxito.");
      } else {
        alert("Error al guardar: " + res.data.message);
      }
    } catch (err) {
      alert("Error al intentar actualizar el remito: " + err.message);
    }
  };

  const handleSendEmail = async (e) => {
    e.preventDefault();
    if (!viewingRemito) return;

    // Buscar imagen en las copias escaneadas
    let archivoRuta = "";
    const copias = ['ocr_duplicado', 'ocr_triplicado', 'ocr_original', 'ocr_cuatriplcado'];
    for (const c of copias) {
      const fieldVal = viewingRemito[c];
      if (fieldVal) {
        try {
          const parsed = typeof fieldVal === 'string' ? JSON.parse(fieldVal) : fieldVal;
          if (parsed && parsed.archivo) {
            archivoRuta = parsed.archivo;
            break;
          }
        } catch (e) { }
      }
    }

    setIsSendingEmail(true);
    try {
      const res = await axios.post(`${apiUrl}/api/send-remito-email`, {
        transaccion_id: viewingRemito.finne_transaccionID,
        archivo_ruta: archivoRuta,
        emails: emailDestinatarios
      });
      if (res.data.status === 'success') {
        alert("Email enviado exitosamente.");
        fetchHistory(currentPage);
      } else {
        alert("Fallo al enviar correo: " + res.data.message);
      }
    } catch (err) {
      alert("Error al enviar email: " + err.message);
    } finally {
      setIsSendingEmail(false);
    }
  };

  const getViewerImageUrl = () => {
    if (!viewingRemito) return "";
    let archivoRuta = "";
    const copias = ['ocr_duplicado', 'ocr_triplicado', 'ocr_original', 'ocr_cuatriplcado'];
    for (const c of copias) {
      const keyName = c.replace('ocr_', '') + '_archivo';
      const pathVal = viewingRemito.copias_escaneadas?.[keyName];
      if (pathVal) {
        archivoRuta = pathVal;
        break;
      }
    }
    if (!archivoRuta) return "";
    const cleanPath = archivoRuta.replace(/\\/g, '/');
    if (cleanPath.startsWith('http://') || cleanPath.startsWith('https://')) {
      return cleanPath;
    }
    return `${apiUrl}/${cleanPath}`;
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchHistory(1);

      // Consultar estado inicial del servidor para sincronizar la interfaz
      const syncStatus = async () => {
        try {
          const res = await axios.get(`${apiUrl}/api/status`);
          setStatus(res.data.status);
          setCancelRequested(res.data.cancel_requested || false);
          if (res.data.status !== 'idle') {
            setShowModal(true);
            setActionStarted(true);
            setProgress({
              message: res.data.progress_message || '',
              current: res.data.current_step || 0,
              total: res.data.total_steps || 0
            });
          } else {
            // Si el servidor ya está idle al arrancar, nos aseguramos de no mostrar modal ni resultados colgados
            setShowModal(false);
            setActionStarted(false);
            setSummaryData(null);
            setCancelRequested(false);
          }
        } catch (err) {
          // Ignorar temporal offline
        }
      };
      syncStatus();
    }
  }, [isAuthenticated, apiUrl]);

  const handleAction = async (endpoint, actionName) => {
    try {
      setStatus(endpoint === 'scan-and-process' ? 'scanning-and-processing' :
        endpoint === 'scan' ? 'scanning' :
          endpoint === 'process' ? 'processing' : 'syncing');
      setProgress({ message: `Iniciando: "${actionName}"...`, current: 0, total: 0 });
      setShowModal(true);
      setActionStarted(true);
      setSummaryData(null);

      const res = await axios.post(`${apiUrl}/api/${endpoint}`);
      if (res.data.status !== 'started') {
        if (res.data.message && res.data.message.includes("ocupado")) {
          if (window.confirm(`${res.data.message}\n\n¿Desea forzar la cancelación y desbloquear el servidor a reposo de inmediato?`)) {
            try {
              // Enviar dos llamadas para forzar la cancelación
              await axios.post(`${apiUrl}/api/cancel`, {});
              const finalRes = await axios.post(`${apiUrl}/api/cancel`, {});
              if (finalRes.data.status === 'forced_idle') {
                setStatus('idle');
                setSummaryData({
                  success: false,
                  cancelled: true,
                  type: 'process',
                  message: "Servidor desbloqueado manualmente. El proceso fue cancelado de forma forzada.",
                  summary: {}
                });
                fetchHistory(currentPage);
                alert("Servidor desbloqueado con éxito.");
                return;
              }
            } catch (cErr) {
              alert("Error al intentar desbloquear el servidor: " + (cErr.response?.data?.message || cErr.message));
            }
          }
        } else {
          alert(`Error al iniciar el proceso: ${res.data.message}`);
        }
        setStatus('idle');
        setShowModal(false);
        setActionStarted(false);
      }
    } catch (err) {
      setStatus('idle');
      setActionStarted(false);
      setShowModal(false);
      alert(`⚠️ Error de comunicación:\n\nNo se pudo establecer conexión con el servidor de remitos en:\n${apiUrl}\n\nPor favor, verifique que el backend esté encendido.\n\nDetalle: ${err.message}`);
    }
  };

  const handleCancel = async () => {
    setShowCancelConfirm(false);
    setCancelRequested(true);
    setProgress(prev => ({ ...prev, message: "Cancelación solicitada, deteniendo de forma limpia..." }));
    try {
      const res = await axios.post(`${apiUrl}/api/cancel`, {});
      if (res.data.status === 'forced_idle') {
        setStatus('idle');
        setSummaryData({
          success: false,
          cancelled: true,
          type: 'process',
          message: "Servidor desbloqueado manualmente. El proceso fue cancelado de forma forzada.",
          summary: {}
        });
        fetchHistory(currentPage);
      }
    } catch (err) {
      alert("Error al enviar la solicitud de cancelación: " + (err.response?.data?.message || err.message));
    }
  };

  // Manejadores de Selección y Envío de Reclamos
  const handleSelectRow = (txId) => {
    setSelectedIds(prev =>
      prev.includes(txId) ? prev.filter(id => id !== txId) : [...prev, txId]
    );
  };

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      const allTxIds = history.map(row => row.transaccion_id);
      setSelectedIds(allTxIds);
    } else {
      setSelectedIds([]);
    }
  };

  const handleSendReclamos = async () => {
    if (selectedIds.length === 0) {
      alert("Por favor, seleccione al menos un remito para reclamar.");
      return;
    }

    setIsReclamando(true);
    setIsPreparingReclaim(true);
    try {
      const res = await axios.post(`${apiUrl}/api/prepare-reclaims`, {
        transaccion_ids: selectedIds
      });
      if (res.data.status === 'success') {
        setReclaimDraft({
          destinatarios: res.data.destinatarios,
          copias: res.data.copias,
          asunto: res.data.asunto,
          cuerpo: res.data.cuerpo
        });
        setActiveReclaimTab('preview');
        setShowReclaimModal(true);
      } else {
        alert(`Ocurrió un error al preparar el borrador de reclamos:\n\n${res.data.message}`);
      }
    } catch (err) {
      alert("Error al conectar con el servidor para preparar reclamos: " + err.message);
    } finally {
      setIsReclamando(false);
      setIsPreparingReclaim(false);
    }
  };

  const handleConfirmSendReclaim = async (e) => {
    e.preventDefault();
    if (!reclaimDraft) return;

    setIsSendingReclaim(true);
    try {
      const res = await axios.post(`${apiUrl}/api/send-prepared-reclaims`, {
        transaccion_ids: selectedIds,
        destinatarios: reclaimDraft.destinatarios,
        copias: reclaimDraft.copias,
        asunto: reclaimDraft.asunto,
        cuerpo: reclaimDraft.cuerpo
      });

      if (res.data.status === 'success') {
        alert("¡Reclamos enviados con éxito!");
        setShowReclaimModal(false);
        setReclaimDraft(null);
        setSelectedIds([]);
        fetchHistory(currentPage);
      } else {
        alert(`Ocurrió un error al enviar los reclamos:\n\n${res.data.message}`);
      }
    } catch (err) {
      alert("Error al intentar enviar los correos de reclamo: " + err.message);
    } finally {
      setIsSendingReclaim(false);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchHistory(1, searchQuery);
  };

  // --- VISTA DE LOGIN ---
  if (!isAuthenticated) {
    return (
      <div className="login-wrapper">
        <div className="login-card glass">
          <div className="login-brand">
            <div className="login-logo">R</div>
            <h2>Don Yeyo S.A.</h2>
            <p>Auditoría de Recepción y Firma de Remitos<br />Acceso exclusivo para personal autorizado</p>
          </div>

          <button className="btn-microsoft-login" onClick={loginMicrosoft}>
            <svg viewBox="0 0 23 23">
              <path fill="#f3f2f1" d="M1 1h10v10H1z" />
              <path fill="#f3f2f1" d="M12 1h10v10H1z" />
              <path fill="#1 12h10v10H1z" />
              <path fill="#12 12h10v10H1z" />
              <path fill="#f25022" d="M1 1h10v10H1z" />
              <path fill="#7fba00" d="M12 1h10v10H12z" />
              <path fill="#00a4ef" d="M1 12h10v10H1z" />
              <path fill="#ffb900" d="M12 12h10v10H12z" />
            </svg>
            Iniciar Sesión con Microsoft
          </button>
        </div>
      </div>
    );
  }

  // --- VISTA PANTALLA COMPLETA: VISUALIZADOR DE REMITO ESCANEADO (CLEAN VIEW) ---
  if (showViewerModal && viewingRemito) {
    return (
      <div style={{
        minHeight: '100vh', background: 'var(--background)', padding: '32px',
        boxSizing: 'border-box', display: 'flex', flexDirection: 'column', gap: 24,
        color: 'var(--text)'
      }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border)', paddingBottom: '16px' }}>
          <div>
            <h1 style={{ fontSize: '24px', fontWeight: 800, margin: 0 }}>Visualizador de Comprobante Escaneado</h1>
            <p style={{ fontSize: '13.5px', color: 'var(--text-muted)', margin: '4px 0 0 0' }}>
              Remito Nro: <strong>{viewingRemito.numero}</strong> | Transacción ID: {viewingRemito.transaccion_id}
            </p>
          </div>
          <button
            className="btn btn-secondary btn-md"
            onClick={() => setShowViewerModal(false)}
            style={{ border: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 8 }}
          >
            ← Volver al Historial
          </button>
        </div>

        {/* Layout Principal del Visor */}
        <div style={{ display: 'flex', gap: 24, flexGrow: 1, minHeight: 0, overflow: 'hidden' }}>

          {/* Contenedor de la Imagen con Zoom */}
          <div style={{
            flexGrow: 1, background: '#090f1e', borderRadius: '20px', border: '1px solid var(--border)',
            position: 'relative', display: 'flex', flexDirection: 'column', overflow: 'hidden'
          }}>
            {/* Controles de Zoom flotantes */}
            <div style={{
              position: 'absolute', top: 16, right: 16, display: 'flex', gap: 8, zIndex: 10,
              background: 'rgba(15, 23, 42, 0.85)', padding: '8px', borderRadius: '10px', border: '1px solid var(--border)'
            }}>
              <button
                className="btn btn-secondary btn-sm"
                style={{ padding: '6px 12px', minWidth: 'auto', fontSize: '14px' }}
                onClick={() => setZoomLevel(prev => Math.max(0.5, prev - 0.25))}
              >
                -
              </button>
              <span style={{ fontSize: '12.5px', fontWeight: 700, display: 'flex', alignItems: 'center', padding: '0 6px' }}>
                {Math.round(zoomLevel * 100)}%
              </span>
              <button
                className="btn btn-secondary btn-sm"
                style={{ padding: '6px 12px', minWidth: 'auto', fontSize: '14px' }}
                onClick={() => setZoomLevel(prev => Math.min(3.0, prev + 0.25))}
              >
                +
              </button>
              <button
                className="btn btn-secondary btn-sm"
                style={{ padding: '6px 10px', minWidth: 'auto', fontSize: '12px' }}
                onClick={() => setZoomLevel(1.0)}
              >
                100%
              </button>
            </div>

            {/* Contenedor de la imagen */}
            <div style={{ flexGrow: 1, overflow: 'auto', padding: '24px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {getViewerImageUrl() ? (
                <img
                  src={getViewerImageUrl()}
                  alt="Remito digitalizado"
                  style={{
                    transform: `scale(${zoomLevel})`,
                    transition: 'transform 0.2s ease',
                    maxHeight: '100%',
                    maxWidth: '100%',
                    objectFit: 'contain',
                    transformOrigin: 'center center'
                  }}
                />
              ) : (
                <div style={{ color: 'var(--text-muted)', fontSize: '14px' }}>
                  Cargando imagen física desde el servidor...
                </div>
              )}
            </div>
          </div>

          {/* Panel Lateral de Envío de Email */}
          <div style={{
            width: '340px', display: 'flex', flexDirection: 'column', gap: 20,
            background: 'var(--surface)', border: '1px solid var(--border)',
            borderRadius: '20px', padding: '24px', boxSizing: 'border-box', flexShrink: 0
          }}>
            <div>
              <h4 style={{ fontSize: '15px', fontWeight: 800, margin: '0 0 6px 0' }}>Reenviar por Email</h4>
              <p style={{ fontSize: '12.5px', color: 'var(--text-muted)', margin: 0, lineHeight: '1.45' }}>
                Envía el escaneo de este remito como un adjunto de correo directo al cliente. Se adjuntará copia (CC) a los correos de auditoría de forma automática.
              </p>
            </div>

            <form onSubmit={handleSendEmail} style={{ display: 'flex', flexDirection: 'column', gap: 16, flexGrow: 1 }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <label style={{ fontSize: '13px', color: 'var(--text-muted)', fontWeight: 700 }}>Destinatarios (Cliente):</label>
                <textarea
                  placeholder="ejemplo@cliente.com"
                  value={emailDestinatarios}
                  onChange={(e) => setEmailDestinatarios(e.target.value)}
                  required
                  style={{
                    height: '110px', resize: 'none', background: 'var(--background)',
                    border: '1px solid var(--border)', color: 'var(--text)', padding: '12px',
                    borderRadius: '10px', fontSize: '13px', fontFamily: 'inherit', lineHeight: 1.4
                  }}
                />
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Múltiples correos separados por comas.</span>
              </div>

              <button
                type="submit"
                disabled={isSendingEmail}
                className="btn btn-primary btn-md"
                style={{ width: '100%', marginTop: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, padding: '12px' }}
              >
                {isSendingEmail ? (
                  <>
                    <Loader size={16} className="spin-animation" />
                    Enviando...
                  </>
                ) : (
                  <>
                    <Mail size={16} />
                    Enviar Remito Escaneado
                  </>
                )}
              </button>
            </form>
          </div>

        </div>
      </div>
    );
  }

  // --- VISTA PANTALLA COMPLETA: PREVISUALIZACIÓN DE RECLAMOS (CLEAN VIEW) ---
  if (showReclaimModal && reclaimDraft) {
    const isBulk = selectedIds.length > 1;
    return (
      <div style={{
        minHeight: '100vh', background: 'var(--background)', padding: '32px',
        boxSizing: 'border-box', display: 'flex', flexDirection: 'column', gap: 24,
        color: 'var(--text)'
      }}>
        {/* Header Superior Limpio */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border)', paddingBottom: '16px' }}>
          <div>
            <h1 style={{ fontSize: '24px', fontWeight: 800, margin: 0 }}>Preparación de Campaña de Reclamo</h1>
            <p style={{ fontSize: '13.5px', color: 'var(--text-muted)', margin: '4px 0 0 0' }}>
              {isBulk ? (
                <>Modo Masivo: Enviando de forma individual a <strong>{selectedIds.length}</strong> clientes con comodines dinámicos.</>
              ) : (
                <>Modo Individual: Reclamando remito de cliente único con datos específicos.</>
              )}
            </p>
          </div>
          <button
            className="btn btn-secondary btn-md"
            onClick={() => setShowReclaimModal(false)}
            style={{ border: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 8 }}
          >
            ← Volver al Historial
          </button>
        </div>

        {/* Layout Principal de Pantalla Completa (Limpio) */}
        <div style={{ display: 'flex', gap: 24, flexGrow: 1, minHeight: 0, overflow: 'hidden' }}>

          {/* Formulario Lateral */}
          <form onSubmit={handleConfirmSendReclaim} style={{
            width: '340px', display: 'flex', flexDirection: 'column', gap: 20,
            background: 'var(--surface)', border: '1px solid var(--border)',
            borderRadius: '20px', padding: '24px', boxSizing: 'border-box', flexShrink: 0
          }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <label style={{ fontSize: '13px', color: 'var(--text-muted)', fontWeight: 700 }}>Destinatarios (Cliente):</label>
              {isBulk ? (
                <div style={{
                  background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border)',
                  color: 'var(--text-muted)', padding: '10px 14px', borderRadius: '8px',
                  fontSize: '13px', fontFamily: 'var(--font-mono)', userSelect: 'none'
                }}>
                  {reclaimDraft.destinatarios}
                </div>
              ) : (
                <input
                  type="text"
                  value={reclaimDraft.destinatarios}
                  onChange={(e) => setReclaimDraft(prev => ({ ...prev, destinatarios: e.target.value }))}
                  required
                  placeholder="correos@cliente.com"
                  style={{
                    background: 'var(--background)', border: '1px solid var(--border)',
                    color: 'var(--text)', padding: '10px 14px', borderRadius: '8px', fontSize: '13px'
                  }}
                />
              )}
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', lineHeight: 1.3 }}>
                {isBulk ? (
                  "En envíos masivos, los emails se extraen de forma automática de Finnegans para cada cliente."
                ) : (
                  "Separe múltiples direcciones por comas si es necesario."
                )}
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <label style={{ fontSize: '13px', color: 'var(--text-muted)', fontWeight: 700 }}>En Copia (Auditoría/CC):</label>
              <input
                type="text"
                value={reclaimDraft.copias}
                onChange={(e) => setReclaimDraft(prev => ({ ...prev, copias: e.target.value }))}
                placeholder="auditoria@miempresa.com"
                style={{
                  background: 'var(--background)', border: '1px solid var(--border)',
                  color: 'var(--text)', padding: '10px 14px', borderRadius: '8px', fontSize: '13px'
                }}
              />
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>emails de copia de control.</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <label style={{ fontSize: '13px', color: 'var(--text-muted)', fontWeight: 700 }}>Asunto del Correo:</label>
              <input
                type="text"
                value={reclaimDraft.asunto}
                onChange={(e) => setReclaimDraft(prev => ({ ...prev, asunto: e.target.value }))}
                required
                style={{
                  background: 'var(--background)', border: '1px solid var(--border)',
                  color: 'var(--text)', padding: '10px 14px', borderRadius: '8px', fontSize: '13px'
                }}
              />
              {isBulk && (
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  Puede utilizar el comodín <code style={{ color: 'var(--primary)' }}>{"{{NUMERO_REMITO}}"}</code>
                </span>
              )}
            </div>

            <button
              type="submit"
              disabled={isSendingReclaim}
              className="btn btn-primary btn-md"
              style={{ width: '100%', marginTop: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, padding: '14px' }}
            >
              {isSendingReclaim ? (
                <>
                  <Loader size={16} className="spin-animation" />
                  Enviando Campaña...
                </>
              ) : (
                <>
                  <Mail size={16} />
                  Enviar Reclamos
                </>
              )}
            </button>
          </form>

          {/* Área de Visualización y Edición de Plantilla */}
          <div style={{
            flexGrow: 1, display: 'flex', flexDirection: 'column', gap: 12,
            background: 'var(--surface)', borderRadius: '20px', border: '1px solid var(--border)',
            overflow: 'hidden'
          }}>
            {/* Control Solapas */}
            <div style={{
              display: 'flex', borderBottom: '1px solid var(--border)', background: 'rgba(255,255,255,0.01)', padding: '8px 16px'
            }}>
              <button
                type="button"
                className={`btn btn-sm ${activeReclaimTab === 'preview' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '8px 16px', borderRadius: '8px', fontSize: '12.5px', minWidth: 'auto' }}
                onClick={() => setActiveReclaimTab('preview')}
              >
                Vista previa
              </button>

              <button
                type="button"
                className={`btn btn-sm ${activeReclaimTab === 'editor' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '8px 16px', borderRadius: '8px', fontSize: '12.5px', minWidth: 'auto', marginLeft: 8 }}
                onClick={() => setActiveReclaimTab('editor')}
              >
                Código editable
              </button>


              <div style={{ marginLeft: 'auto', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '3px' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', opacity: 0.85 }}>
                  Plantilla base: <code style={{ color: 'var(--primary)', fontStyle: 'normal' }}>server/templates/reclamo_template.html</code>
                </span>
                {isBulk && (
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    Comodines: <code style={{ color: 'var(--primary)', marginLeft: 4 }}>{"{{CLIENTE}}"}</code>, <code style={{ color: 'var(--primary)', marginLeft: 4 }}>{"{{NUMERO_REMITO}}"}</code>, <code style={{ color: 'var(--primary)', marginLeft: 4 }}>{"{{IMPORTE}}"}</code>
                  </span>
                )}
              </div>
            </div>

            {/* Contenedor Editor/Render */}
            <div style={{ flexGrow: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
              {activeReclaimTab === 'editor' ? (
                <textarea
                  value={reclaimDraft.cuerpo}
                  onChange={(e) => setReclaimDraft(prev => ({ ...prev, cuerpo: e.target.value }))}
                  required
                  style={{
                    width: '100%', height: '100%', resize: 'none', background: 'transparent',
                    border: 'none', color: '#a6accd', padding: '24px', boxSizing: 'border-box',
                    fontFamily: 'var(--font-mono)', fontSize: '13px', lineHeight: 1.55,
                    outline: 'none'
                  }}
                />
              ) : (
                <iframe
                  title="Previsualización de Correo de Reclamo"
                  srcDoc={reclaimDraft.cuerpo}
                  style={{
                    width: '100%', height: '100%', border: 'none', background: '#ffffff'
                  }}
                />
              )}
            </div>
          </div>

        </div>
      </div>
    );
  }

  // Flags para visibilidad de tarjetas de acción (por defecto true, se ocultan con 'false')
  const mostrarEscanProcTodo = import.meta.env.VITE_MOSTRAR_ESCAN_PROC_TODO !== 'false';
  const mostrarEscanMasivo = import.meta.env.VITE_MOSTRAR_ESCAN_MASIVO !== 'false';
  const mostrarProcesarIa = import.meta.env.VITE_MOSTRAR_PROCESAR_IA !== 'false';
  const mostrarActualizaRemitos = import.meta.env.VITE_MOSTRAR_ACTUALIZA_REMITOS !== 'false';

  // --- VISTA PRINCIPAL (DASHBOARD) ---
  return (
    <div className="app-wrapper">
      {/* Header */}
      <header className="app-header glass">
        <div className="brand-section">
          <div className="brand-logo">R</div>
          <div className="brand-title">
            <h1>Firma de Remitos</h1>
            <p>Don Yeyo S.A. — v{appVersion}</p>
          </div>
        </div>

        <div className="user-profile">
          <div className="user-info desktop-only" style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '2px' }}>
            <div className="user-name" style={{ lineHeight: 1.2 }}>{user?.name}</div>
            <div className="user-email" style={{ lineHeight: 1.2 }}>{user?.email}</div>
          </div>

          <button
            className="btn btn-secondary btn-sm"
            style={{ borderRadius: '50%', padding: '8px', minWidth: '38px', minHeight: '38px' }}
            onClick={() => setIsDark(!isDark)}
            title="Alternar Tema Claro/Oscuro"
          >
            {isDark ? <Sun size={16} /> : <Moon size={16} />}
          </button>

          <button
            className="btn btn-secondary btn-sm"
            style={{ borderRadius: '50%', padding: '8px', minWidth: '38px', minHeight: '38px' }}
            onClick={() => setIsConfigOpen(!isConfigOpen)}
            title="Configurar Red LAN"
          >
            <Settings size={16} />
          </button>

          <button className="btn btn-secondary btn-sm btn-logout" onClick={logout}>
            <LogOut size={14} />
            Salir
          </button>
        </div>
      </header>

      {/* Modal Configuración IP */}
      {isConfigOpen && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, width: '100%', height: '100%',
          background: 'rgba(15, 23, 42, 0.75)', display: 'flex', alignItems: 'center',
          justifyContent: 'center', zIndex: 10000, padding: '20px'
        }}>
          <form onSubmit={saveApiConfig} className="glass" style={{
            width: '100%', maxWidth: '400px', padding: '30px', display: 'flex',
            flexDirection: 'column', gap: 20, borderRadius: 'var(--radius)'
          }}>
            <h3 style={{ fontSize: '18px', fontWeight: 700 }}>Configuración de Red LAN</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <label style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Dirección del Servidor:</label>
              <input
                type="text"
                value={tempApiUrl}
                onChange={(e) => setTempApiUrl(e.target.value)}
                style={{
                  background: 'var(--background)', border: '1px solid var(--border)',
                  color: 'var(--text)', padding: '12px', borderRadius: '8px', fontSize: '14px',
                  fontFamily: 'var(--font-mono)'
                }}
              />
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                Ejemplo: http://192.168.1.100:8000
              </span>
            </div>

            <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end', marginTop: 10 }}>
              <button
                type="button"
                onClick={() => setIsConfigOpen(false)}
                className="btn btn-secondary btn-sm"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="btn btn-primary btn-sm"
              >
                Guardar
              </button>
            </div>
          </form>
        </div>
      )}

      {/* MODAL DE PROGRESO Y RESUMEN A PANTALLA COMPLETA */}
      {showModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, width: '100%', height: '100%',
          background: 'rgba(15, 23, 42, 0.85)', display: 'flex', alignItems: 'center',
          justifyContent: 'center', zIndex: 10000, padding: '24px', backdropFilter: 'blur(12px)'
        }}>
          <div className="glass" style={{
            width: '100%', maxWidth: '480px', padding: '36px', borderRadius: '24px',
            textAlign: 'center', display: 'flex', flexDirection: 'column', gap: 24,
            boxShadow: 'var(--shadow-lg)'
          }}>
            {!summaryData ? (
              showCancelConfirm ? (
                // --- SUB-VISTA: CONFIRMACIÓN DE CANCELACIÓN ---
                <>
                  <div style={{ display: 'flex', justifyContent: 'center', color: 'var(--warning)' }}>
                    <XCircle size={58} />
                  </div>
                  <div>
                    <h2 style={{ fontSize: '20px', fontWeight: 800, marginBottom: 8 }}>¿Cancelar Operación?</h2>
                    <p style={{ fontSize: '13.5px', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                      Esta acción detendrá de manera segura el lote en el próximo punto libre. No se dejarán archivos corruptos ni inconsistencias en la base de datos.
                    </p>
                  </div>
                  <div style={{ display: 'flex', gap: 12, width: '100%' }}>
                    <button
                      onClick={() => setShowCancelConfirm(false)}
                      className="btn btn-primary btn-md"
                      style={{ flex: 1, padding: '10px 16px' }}
                    >
                      No, Continuar
                    </button>
                    <button
                      onClick={handleCancel}
                      className="btn btn-secondary btn-md"
                      style={{ flex: 1, padding: '10px 16px', border: '1px solid var(--border)', color: 'var(--error)' }}
                    >
                      Sí, Cancelar
                    </button>
                  </div>
                </>
              ) : (
                // --- VISTA 1: PROCESANDO NORMAL ---
                <>
                  <div style={{ display: 'flex', justifyContent: 'center' }}>
                    <Loader
                      size={54}
                      className="spin-animation"
                      style={{ animation: 'spin 1.5s linear infinite', color: 'var(--primary)' }}
                    />
                  </div>
                  <div>
                    <h2 style={{ fontSize: '22px', fontWeight: 800, marginBottom: 8 }}>Procesando...</h2>
                    <p style={{ fontSize: '14.5px', color: 'var(--text)', fontWeight: 500, minHeight: '40px' }}>
                      {progress.message || 'Estableciendo enlace de comunicación...'}
                    </p>

                    {/* Barra de progreso visual */}
                    <div style={{
                      width: '100%', height: '8px', background: 'rgba(255, 255, 255, 0.1)',
                      borderRadius: '4px', marginTop: '16px', overflow: 'hidden', position: 'relative'
                    }}>
                      {progress.total > 0 ? (
                        <div style={{
                          width: `${(progress.current / progress.total) * 100}%`, height: '100%',
                          background: 'var(--primary)', transition: 'width 0.4s ease'
                        }} />
                      ) : (
                        <div className="shimmer-progress-bar" style={{
                          width: '45%', height: '100%',
                          position: 'absolute', top: 0, left: 0,
                          animation: 'shimmer 1.8s infinite linear'
                        }} />
                      )}
                    </div>
                  </div>

                  <button
                    onClick={() => setShowCancelConfirm(true)}
                    className="btn btn-secondary btn-md"
                    disabled={cancelRequested}
                    style={{
                      width: '100%',
                      border: '1px solid var(--border)',
                      color: cancelRequested ? 'var(--text-muted)' : 'var(--error)',
                      cursor: cancelRequested ? 'not-allowed' : 'pointer'
                    }}
                  >
                    {cancelRequested ? 'Cancelación en curso...' : 'Cancelar Proceso'}
                  </button>
                </>
              )
            ) : (
              // --- VISTA 2: RESUMEN FINAL ---
              <>
                <div style={{ display: 'flex', justifyContent: 'center', color: summaryData.success ? 'var(--success)' : summaryData.cancelled ? 'var(--warning)' : 'var(--error)' }}>
                  {summaryData.success ? <CheckCircle size={58} /> : <XCircle size={58} />}
                </div>
                <div>
                  <h2 style={{ fontSize: '22px', fontWeight: 800, marginBottom: 4 }}>
                    {summaryData.cancelled ? 'Proceso Cancelado' : summaryData.success ? 'Proceso Finalizado' : 'Error en Proceso'}
                  </h2>
                  {summaryData.message && (
                    <p style={{ fontSize: '13.5px', color: 'var(--error)', marginTop: 8 }}>
                      {summaryData.message}
                    </p>
                  )}
                </div>

                {/* Cuadro de Estadísticas adaptativo */}
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 12,
                  background: 'var(--surface-hover)',
                  padding: '20px',
                  borderRadius: '16px',
                  border: '1px solid var(--border)',
                  width: '100%',
                  boxSizing: 'border-box'
                }}>
                  {summaryData.type === 'syncing' ? (
                    <>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', fontSize: '13.5px' }}>
                        <span style={{ textAlign: 'left', color: 'var(--text-muted)' }}>Remitos encontrados en ERP:</span>
                        <strong style={{ textAlign: 'right', color: 'var(--text)' }}>{summaryData.summary.erp_encontrados || 0}</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', fontSize: '13.5px' }}>
                        <span style={{ textAlign: 'left', color: 'var(--text-muted)' }}>Nuevos registrados:</span>
                        <strong style={{ textAlign: 'right', color: 'var(--success)' }}>{summaryData.summary.erp_nuevos || 0}</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', fontSize: '13.5px' }}>
                        <span style={{ textAlign: 'left', color: 'var(--text-muted)' }}>Existentes actualizados:</span>
                        <strong style={{ textAlign: 'right', color: 'var(--primary)' }}>{summaryData.summary.erp_actualizados || 0}</strong>
                      </div>
                    </>
                  ) : (
                    <>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', fontSize: '13.5px' }}>
                        <span style={{ textAlign: 'left', color: 'var(--text-muted)' }}>Páginas escaneadas:</span>
                        <strong style={{ textAlign: 'right', color: 'var(--text)' }}>{summaryData.summary.escaneados || 0}</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', fontSize: '13.5px' }}>
                        <span style={{ textAlign: 'left', color: 'var(--text-muted)' }}>Remitos analizados por Agente:</span>
                        <strong style={{ textAlign: 'right', color: 'var(--success)' }}>{summaryData.summary.exitosasIa || 0}</strong>
                      </div>
                      {summaryData.summary.fallidosIa > 0 && (
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', fontSize: '13.5px', color: 'var(--error)' }}>
                          <span style={{ textAlign: 'left' }}>Análisis IA fallidos:</span>
                          <strong style={{ textAlign: 'right' }}>{summaryData.summary.fallidosIa}</strong>
                        </div>
                      )}
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', fontSize: '13.5px' }}>
                        <span style={{ textAlign: 'left', color: 'var(--text-muted)' }}>Registros guardados:</span>
                        <strong style={{ textAlign: 'right', color: 'var(--primary)' }}>{summaryData.summary.bdActualizados || 0}</strong>
                      </div>
                      {summaryData.summary.bdNoEncontrados > 0 && (
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', fontSize: '13.5px', color: 'var(--warning)' }}>
                          <span style={{ textAlign: 'left' }}>No encontrados en BD (sin ERP):</span>
                          <strong style={{ textAlign: 'right' }}>{summaryData.summary.bdNoEncontrados}</strong>
                        </div>
                      )}
                    </>
                  )}
                </div>

                <button
                  onClick={() => {
                    setShowModal(false);
                    setActionStarted(false);
                    setSummaryData(null);
                  }}
                  className="btn btn-primary btn-md"
                  style={{ width: '100%' }}
                >
                  Cerrar
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {/* Navegación por Solapas (Tabs) */}
      <div className="tab-navigation glass desktop-only" style={{
        display: 'flex', gap: 12, padding: '8px', margin: '20px auto 30px auto',
        width: 'fit-content', borderRadius: '50px', border: '1px solid var(--border)'
      }}>
        <button
          className={`btn ${activeTab === 'actions' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ borderRadius: '50px', padding: '10px 24px', fontSize: '13.5px', fontWeight: 600 }}
          onClick={() => setActiveTab('actions')}
        >
          Botonera
        </button>
        <button
          className={`btn ${activeTab === 'history' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ borderRadius: '50px', padding: '10px 24px', fontSize: '13.5px', fontWeight: 600 }}
          onClick={() => {
            setActiveTab('history');
            fetchHistory(currentPage);
          }}
        >
          Remitos ({totalItems})
        </button>
        <button
          className={`btn ${activeTab === 'stats' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ borderRadius: '50px', padding: '10px 24px', fontSize: '13.5px', fontWeight: 600 }}
          onClick={() => {
            setActiveTab('stats');
            fetchStats();
          }}
        >
          Dashboard
        </button>
      </div>

      {activeTab === 'actions' ? (
        // --- SECCIÓN: ACCIONES PRINCIPALES ---
        <main className="actions-section">
          {/* Flujo Completo */}
          {mostrarEscanProcTodo && (
            <div
              className="action-card glass full-width"
              role="button"
              tabIndex={0}
              onClick={() => handleAction('scan-and-process', 'Escanear + Procesar Todo')}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handleAction('scan-and-process', 'Escanear + Procesar Todo');
                }
              }}
            >
              <div className="action-icon">
                <Play size={20} />
              </div>
              <div>
                <h3>Escanear + Procesar Todo</h3>
                <p>Jala los remitos del alimentador de la Ricoh, los digitaliza e inicia el análisis automático por IA para firmar en base de datos y SharePoint en un solo paso.</p>
              </div>
            </div>
          )}

          {/* Paso 1: Escaneo */}
          {mostrarEscanMasivo && (
            <div
              className="action-card glass"
              role="button"
              tabIndex={0}
              onClick={() => handleAction('scan', 'Escaneo Masivo (Paso 1)')}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handleAction('scan', 'Escaneo Masivo (Paso 1)');
                }
              }}
            >
              <div className="action-icon">
                <Printer size={18} />
              </div>
              <div>
                <h3>Escaneo Masivo</h3>
                <p>Paso 1: Jala los papeles de la bandeja física del escáner y los almacena en formato JPG.</p>
              </div>
            </div>
          )}

          {/* Paso 2: Procesar IA */}
          {mostrarProcesarIa && (
            <div
              className="action-card glass"
              role="button"
              tabIndex={0}
              onClick={() => handleAction('process', 'Procesar Imágenes (Paso 2)')}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handleAction('process', 'Procesar Imágenes (Paso 2)');
                }
              }}
            >
              <div className="action-icon">
                <Cpu size={18} />
              </div>
              <div>
                <h3>Procesar por IA</h3>
                <p>Paso 2: Analiza las imágenes digitalizadas en busca de firmas y sellos con IA.</p>
              </div>
            </div>
          )}

          {/* Finnegans Sync */}
          {mostrarActualizaRemitos && (
            <div
              className="action-card glass"
              style={{ gridColumn: '1 / -1' }}
              role="button"
              tabIndex={0}
              onClick={() => setShowSyncConfirmModal(true)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  setShowSyncConfirmModal(true);
                }
              }}
            >
              <div className="action-icon">
                <RefreshCw size={18} />
              </div>
              <div>
                <h3>Actualizar remitos desde ERP</h3>
                <p>Sincroniza y descarga los nuevos remitos facturados en Finnegans a la base de datos de auditoría.</p>
              </div>
            </div>
          )}
        </main>
      ) : activeTab === 'history' ? (
        // --- SECCIÓN: HISTORIAL DE AUDITORÍA ---
        <section className="history-section glass" style={{ maxWidth: '1200px', margin: '0 auto 40px auto', padding: '24px' }}>
          <div className="history-header" style={{ marginBottom: 20, display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <Clock size={20} className="text-muted" />
              <h2 style={{ fontSize: '20px', fontWeight: 700 }}>Historial de Remitos</h2>
            </div>

            {/* Buscador en el servidor */}
            <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: 8, flexGrow: 1, maxWidth: '400px' }}>
              <div style={{ position: 'relative', flexGrow: 1 }}>
                <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                <input
                  type="text"
                  placeholder="Buscar Nro, Cliente o Transacción ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{
                    width: '100%', padding: '10px 12px 10px 36px', borderRadius: '30px',
                    background: 'var(--surface-hover)', border: '1px solid var(--border)',
                    color: 'var(--text)', fontSize: '13.5px', boxSizing: 'border-box'
                  }}
                />
              </div>
              <button type="submit" className="btn btn-secondary btn-sm" style={{ borderRadius: '30px', padding: '0 16px' }}>
                Buscar
              </button>
            </form>

            <div style={{ display: 'flex', gap: 10 }}>
              <button
                className="btn btn-primary btn-sm"
                onClick={handleSendReclamos}
                disabled={selectedIds.length === 0 || isReclamando}
                style={{ display: 'flex', alignItems: 'center', gap: 6 }}
              >
                {isReclamando ? <Loader size={12} className="spin-animation" /> : <Mail size={14} />}
                Enviar Reclamos ({selectedIds.length})
              </button>
              <button className="btn btn-secondary btn-sm" onClick={() => fetchHistory(currentPage)} disabled={isHistoryLoading}>
                <RefreshCw size={12} className={isHistoryLoading ? 'spin-animation' : ''} style={{ animation: isHistoryLoading ? 'spin 1.5s linear infinite' : 'none' }} />
                &nbsp;Actualizar
              </button>
            </div>
          </div>

          <div className="history-table-wrapper" style={{ overflowX: 'auto', borderRadius: '12px', border: '1px solid var(--border)' }}>
            <table className="history-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th style={{ width: '40px', padding: '12px' }}>
                    <input
                      type="checkbox"
                      onChange={handleSelectAll}
                      checked={history.length > 0 && selectedIds.length === history.length}
                      style={{ cursor: 'pointer' }}
                    />
                  </th>
                  <th className="col-transaccion" style={{ padding: '12px', textAlign: 'left', cursor: 'pointer', userSelect: 'none' }} onClick={() => handleSort('transaccion_id')}>Transacción ID {renderSortIcon('transaccion_id')}</th>
                  <th className="col-numero" style={{ padding: '12px', textAlign: 'left', cursor: 'pointer', userSelect: 'none' }} onClick={() => handleSort('numero')}>Número Remito {renderSortIcon('numero')}</th>
                  <th className="col-cliente" style={{ padding: '12px', textAlign: 'left', cursor: 'pointer', userSelect: 'none' }} onClick={() => handleSort('cliente')}>Razón Social {renderSortIcon('cliente')}</th>
                  <th className="col-fecha" style={{ padding: '12px', textAlign: 'left', cursor: 'pointer', userSelect: 'none' }} onClick={() => handleSort('fecha')}>Fecha Emisión {renderSortIcon('fecha')}</th>
                  <th className="col-ejemplares" style={{ padding: '12px', textAlign: 'center', cursor: 'pointer', userSelect: 'none' }} onClick={() => handleSort('copias')}>Ejemplares {renderSortIcon('copias')}</th>
                  <th className="col-ol" style={{ padding: '12px', textAlign: 'center', cursor: 'pointer', userSelect: 'none' }} onClick={() => handleSort('confirmado_cliente')}>Firma OL {renderSortIcon('confirmado_cliente')}</th>
                  <th className="col-dist" style={{ padding: '12px', textAlign: 'center', cursor: 'pointer', userSelect: 'none' }} onClick={() => handleSort('confirmado_distribuidor')}>Firma Dist. {renderSortIcon('confirmado_distribuidor')}</th>
                  <th className="col-reclamado" style={{ padding: '12px', textAlign: 'center', cursor: 'pointer', userSelect: 'none' }} onClick={() => handleSort('reclamado')}>Reclamado {renderSortIcon('reclamado')}</th>
                  <th className="col-acciones" style={{ padding: '12px', textAlign: 'center', width: '100px' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {isHistoryLoading ? (
                  <tr>
                    <td colSpan="10" style={{ textAlign: 'center', padding: '60px' }}>
                      <Loader size={32} className="spin-animation" style={{ animation: 'spin 1.5s linear infinite', color: 'var(--primary)' }} />
                      <p style={{ marginTop: 12, color: 'var(--text-muted)', fontSize: '13.5px' }}>Cargando remitos del servidor...</p>
                    </td>
                  </tr>
                ) : history.length === 0 ? (
                  <tr>
                    <td colSpan="10" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '50px' }}>
                      No se encontraron registros de remitos coincidentes.
                    </td>
                  </tr>
                ) : (
                  history.map((row) => (
                    <tr
                      key={row.transaccion_id}
                      className={selectedIds.includes(row.transaccion_id) ? 'selected-row' : ''}
                      style={{ borderBottom: '1px solid var(--border)', cursor: 'pointer' }}
                      onClick={() => handleSelectRow(row.transaccion_id)}
                    >
                      <td style={{ padding: '12px', textAlign: 'center' }} onClick={(e) => e.stopPropagation()}>
                        <input
                          type="checkbox"
                          checked={selectedIds.includes(row.transaccion_id)}
                          onChange={() => handleSelectRow(row.transaccion_id)}
                          style={{ cursor: 'pointer' }}
                        />
                      </td>
                      <td className="col-transaccion" style={{ padding: '12px', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{row.transaccion_id}</td>
                      <td className="col-numero" style={{ padding: '12px', fontWeight: 500 }}>{row.numero}</td>
                      <td className="col-cliente" style={{ padding: '12px', maxWidth: '240px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{row.cliente}</td>
                      <td className="col-fecha" style={{ padding: '12px' }}>{row.fecha}</td>
                      <td className="col-ejemplares" style={{ padding: '12px', textAlign: 'center' }}>
                        <div className="copia-indicators" style={{ display: 'inline-flex', gap: 4 }}>
                          <span className={`copia-dot ${row.copias_escaneadas.original ? 'present' : 'absent'}`} title="Original">O</span>
                          <span className={`copia-dot ${row.copias_escaneadas.duplicado ? 'present' : 'absent'}`} title="Duplicado">D</span>
                          <span className={`copia-dot ${row.copias_escaneadas.triplicado ? 'present' : 'absent'}`} title="Triplicado">T</span>
                          <span className={`copia-dot ${row.copias_escaneadas.cuatriplicado ? 'present' : 'absent'}`} title="Cuatriplicado">C</span>
                        </div>
                      </td>
                      <td className="col-ol" style={{ padding: '12px', textAlign: 'center' }}>
                        {row.copias === 2 ? (
                          <span className="badge-verification not-required">no req.</span>
                        ) : (
                          <span className={`badge-verification ${row.confirmado_cliente ? 'verified' : 'pending'}`}>
                            {row.confirmado_cliente ? 'Sí' : 'No'}
                          </span>
                        )}
                      </td>
                      <td className="col-dist" style={{ padding: '12px', textAlign: 'center' }}>
                        <span className={`badge-verification ${row.confirmado_distribuidor ? 'verified' : 'pending'}`}>
                          {row.confirmado_distribuidor ? 'Sí' : 'No'}
                        </span>
                      </td>
                      <td className="col-reclamado" style={{ padding: '12px', textAlign: 'center' }}>
                        {row.reclamado ? (
                          <span
                            className="badge-verification verified"
                            style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b', display: 'inline-flex', flexDirection: 'column', padding: '4px 8px', borderRadius: '6px' }}
                            title={`Reclamado el: ${row.fecha_ultimo_reclamo}`}
                          >
                            <span>Sí</span>
                            <span style={{ fontSize: '8px', opacity: 0.8 }}>{row.fecha_ultimo_reclamo}</span>
                          </span>
                        ) : (
                          <span className="badge-verification pending">No</span>
                        )}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'center' }} onClick={(e) => e.stopPropagation()}>
                        <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
                          <button
                            title="Editar remito"
                            onClick={() => {
                              setEditingRemito({ ...row });
                              setShowEditModal(true);
                            }}
                            className="btn btn-secondary btn-sm"
                            style={{ padding: '6px 8px', minWidth: 'auto', border: '1px solid var(--border)' }}
                          >
                            <Edit size={13} />
                          </button>
                          {(row.copias_escaneadas.original || row.copias_escaneadas.duplicado || row.copias_escaneadas.triplicado || row.copias_escaneadas.cuatriplicado) ? (
                            <button
                              title="Visualizar imagen escaneada"
                              onClick={async () => {
                                setViewingRemito(row);
                                setZoomLevel(1.0);
                                setEmailDestinatarios('Cargando emails del cliente...');
                                setShowViewerModal(true);
                                try {
                                  const res = await axios.post(`${apiUrl}/api/prepare-reclaims`, {
                                    transaccion_ids: [row.transaccion_id]
                                  });
                                  if (res.data.status === 'success') {
                                    setEmailDestinatarios(res.data.destinatarios || '');
                                  } else {
                                    setEmailDestinatarios('');
                                  }
                                } catch (e) {
                                  console.error("Error al obtener emails del cliente:", e);
                                  setEmailDestinatarios('');
                                }
                              }}
                              className="btn btn-primary btn-sm"
                              style={{ padding: '6px 8px', minWidth: 'auto' }}
                            >
                              <Eye size={13} />
                            </button>
                          ) : (
                            <button
                              disabled
                              title="Sin imagen disponible"
                              className="btn btn-secondary btn-sm"
                              style={{ padding: '6px 8px', minWidth: 'auto', opacity: 0.4, cursor: 'not-allowed' }}
                            >
                              <Eye size={13} style={{ color: 'var(--text-muted)' }} />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Controles de Paginación */}
          {totalPages > 1 && (
            <div className="pagination-controls" style={{
              display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 16, marginTop: 24
            }}>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => fetchHistory(currentPage - 1)}
                disabled={currentPage === 1 || isHistoryLoading}
                style={{ padding: '8px 12px', display: 'flex', alignItems: 'center', gap: 4 }}
              >
                <ChevronLeft size={14} /> Anterior
              </button>

              <span style={{ fontSize: '13.5px', fontWeight: 600, color: 'var(--text-muted)' }}>
                Página <strong style={{ color: 'var(--text)' }}>{currentPage}</strong> de {totalPages}
              </span>

              <button
                className="btn btn-secondary btn-sm"
                onClick={() => fetchHistory(currentPage + 1)}
                disabled={currentPage === totalPages || isHistoryLoading}
                style={{ padding: '8px 12px', display: 'flex', alignItems: 'center', gap: 4 }}
              >
                Siguiente <ChevronRight size={14} />
              </button>
            </div>
          )}
        </section>
      ) : (
        // --- SECCIÓN: ESTADÍSTICAS Y CONTROL (DASHBOARD) ---
        <section className="stats-section glass" style={{ maxWidth: '1200px', margin: '0 auto 40px auto', padding: '30px', borderRadius: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
            <Settings size={22} className="text-primary" />
            <h2 style={{ fontSize: '22px', fontWeight: 800, margin: 0 }}>Dashboard de Auditoría</h2>
          </div>

          {isStatsLoading ? (
            <div style={{ textAlign: 'center', padding: '80px' }}>
              <Loader size={36} className="spin-animation" style={{ color: 'var(--primary)' }} />
              <p style={{ marginTop: 12, color: 'var(--text-muted)' }}>Calculando indicadores en tiempo real desde el ERP y la base de datos...</p>
            </div>
          ) : !dashboardStats ? (
            <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '50px' }}>
              No hay datos estadísticos disponibles.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
              {/* KPIs Grid */}
              <div className="stats-grid" style={{
                display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 20
              }}>
                <div className="glass-card" style={{ padding: '20px', borderRadius: '16px', border: '1px solid var(--border)', textAlign: 'center' }}>
                  <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', fontWeight: 600 }}>Remitos Totales</span>
                  <h3 style={{ fontSize: '32px', fontWeight: 800, marginTop: 8, marginBottom: 0, color: 'var(--text)' }}>{dashboardStats.total_remitos}</h3>
                </div>
                <div className="glass-card" style={{ padding: '20px', borderRadius: '16px', border: '1px solid var(--border)', textAlign: 'center' }}>
                  <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', fontWeight: 600 }}>Firma OL (Cliente)</span>
                  <h3 style={{ fontSize: '32px', fontWeight: 800, marginTop: 8, marginBottom: 0, color: 'var(--success)' }}>{dashboardStats.confirmados_cliente}</h3>
                </div>
                <div className="glass-card" style={{ padding: '20px', borderRadius: '16px', border: '1px solid var(--border)', textAlign: 'center' }}>
                  <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', fontWeight: 600 }}>Firma Distribuidor</span>
                  <h3 style={{ fontSize: '32px', fontWeight: 800, marginTop: 8, marginBottom: 0, color: 'var(--primary)' }}>{dashboardStats.confirmados_distribuidor}</h3>
                </div>
                <div className="glass-card" style={{ padding: '20px', borderRadius: '16px', border: '1px solid var(--border)', textAlign: 'center' }}>
                  <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', fontWeight: 600 }}>Auditoría Completa (OK)</span>
                  <h3 style={{ fontSize: '32px', fontWeight: 800, marginTop: 8, marginBottom: 0, color: '#10b981' }}>{dashboardStats.auditoria_completa}</h3>
                </div>
                <div className="glass-card" style={{ padding: '20px', borderRadius: '16px', border: '1px solid var(--border)', textAlign: 'center' }}>
                  <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', fontWeight: 600 }}>Total Reclamados</span>
                  <h3 style={{ fontSize: '32px', fontWeight: 800, marginTop: 8, marginBottom: 0, color: '#f59e0b' }}>{dashboardStats.total_reclamados}</h3>
                </div>
              </div>

              {/* Tasa y Distribución */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 24 }}>
                {/* Tasa de Digitalización */}
                <div className="glass-card" style={{ padding: '24px', borderRadius: '16px', border: '1px solid var(--border)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 16 }}>
                  <h4 style={{ fontSize: '15px', fontWeight: 700, margin: 0, color: 'var(--text-muted)' }}>Tasa de Digitalización</h4>
                  <div style={{ position: 'relative', width: '120px', height: '120px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <div style={{
                      position: 'absolute', width: '100%', height: '100%', borderRadius: '50%',
                      background: `conic-gradient(var(--primary) ${dashboardStats.tasa_digitalizacion}%, rgba(255,255,255,0.05) ${dashboardStats.tasa_digitalizacion}%)`
                    }} />
                    <div style={{
                      position: 'absolute', width: '88%', height: '88%', borderRadius: '50%',
                      background: 'var(--surface-hover)', display: 'flex', alignItems: 'center', justifyContent: 'center'
                    }}>
                      <span style={{ fontSize: '20px', fontWeight: 800 }}>{dashboardStats.tasa_digitalizacion}%</span>
                    </div>
                  </div>
                  <p style={{ fontSize: '13px', color: 'var(--text-muted)', textAlign: 'center', margin: 0, lineHeight: 1.4 }}>
                    Porcentaje de remitos en el sistema que cuentan con al menos un ejemplar digitalizado físicamente.
                  </p>
                </div>

                {/* Distribución de Ejemplares */}
                <div className="glass-card" style={{ padding: '24px', borderRadius: '16px', border: '1px solid var(--border)', display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <h4 style={{ fontSize: '15px', fontWeight: 700, margin: 0, color: 'var(--text-muted)' }}>Ejemplares Digitalizados</h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                    {[
                      { key: 'original', name: 'Original (OL/Firma Cliente)', color: 'var(--success)' },
                      { key: 'duplicado', name: 'Duplicado (Firma Distribuidor)', color: 'var(--primary)' },
                      { key: 'triplicado', name: 'Triplicado (Firma Chofer)', color: '#f59e0b' },
                      { key: 'cuatriplicado', name: 'Cuatriplicado (Extra)', color: '#a855f7' }
                    ].map(item => {
                      const count = dashboardStats.copias[item.key] || 0;
                      const pct = dashboardStats.total_remitos > 0 ? (count / dashboardStats.total_remitos * 100) : 0;
                      return (
                        <div key={item.key} style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                            <span style={{ color: 'var(--text-muted)' }}>{item.name}</span>
                            <span style={{ fontWeight: 600 }}>{count} ({Math.round(pct * 10) / 10}%)</span>
                          </div>
                          <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', overflow: 'hidden' }}>
                            <div style={{ width: `${pct}%`, height: '100%', background: item.color, borderRadius: '3px', transition: 'width 0.4s ease' }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Top 10 Deudores de Firmas */}
              <div className="glass-card" style={{ padding: '28px', borderRadius: '16px', border: '1px solid var(--border)', display: 'flex', flexDirection: 'column', gap: 20 }}>
                <div>
                  <h4 style={{ fontSize: '15px', fontWeight: 800, margin: '0 0 4px 0' }}>Top 10 Clientes con Mayor Deuda de Firmas</h4>
                  <p style={{ fontSize: '12.5px', color: 'var(--text-muted)', margin: 0, lineHeight: 1.4 }}>
                    Listado de clientes con más firmas pendientes.
                  </p>
                </div>

                {dashboardStats.top_deudores && dashboardStats.top_deudores.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                    {dashboardStats.top_deudores.map((deudor, idx) => {
                      const maxDeuda = dashboardStats.top_deudores[0].deuda || 1;
                      const percent = (deudor.deuda / maxDeuda) * 100;
                      return (
                        <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                          {/* Nro de Puesto */}
                          <div style={{
                            width: '28px', height: '28px', borderRadius: '50%',
                            background: idx === 0 ? 'rgba(239, 68, 68, 0.15)' : idx === 1 ? 'rgba(245, 158, 11, 0.12)' : 'rgba(255,255,255,0.03)',
                            color: idx === 0 ? '#ef4444' : idx === 1 ? '#f59e0b' : 'var(--text-muted)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            fontSize: '12px', fontWeight: 800, border: '1px solid var(--border)', flexShrink: 0
                          }}>
                            {idx + 1}
                          </div>

                          {/* Razón Social y Barra */}
                          <div style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', gap: 6 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13.5px' }}>
                              <span style={{ fontWeight: 600, color: 'var(--text)' }}>{deudor.cliente}</span>
                              <span style={{ fontWeight: 800, color: idx === 0 ? '#ef4444' : 'var(--text)' }}>{deudor.deuda} {deudor.deuda === 1 ? 'remito' : 'remitos'}</span>
                            </div>
                            <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.03)', borderRadius: '3px', overflow: 'hidden' }}>
                              <div style={{
                                width: `${percent}%`, height: '100%',
                                background: idx === 0 ? 'linear-gradient(90deg, var(--primary), #ef4444)' : 'var(--primary)',
                                borderRadius: '3px', transition: 'width 0.4s ease'
                              }} />
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div style={{ color: 'var(--text-muted)', fontSize: '13px', textAlign: 'center', padding: '20px' }}>
                    No hay clientes con deudas de firmas registradas en este momento. ¡Excelente!
                  </div>
                )}
              </div>
            </div>
          )}
        </section>
      )}

      {/* MODAL DE EDICIÓN (FICHA REGISTRO) */}
      {showEditModal && editingRemito && (
        <div style={{
          position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
          background: 'rgba(15, 23, 42, 0.85)', display: 'flex', alignItems: 'center',
          justifyContent: 'center', zIndex: 10000, padding: '24px', backdropFilter: 'blur(12px)'
        }}>
          <div className="glass" style={{
            width: '100%', maxWidth: '520px', padding: '36px', borderRadius: '24px',
            display: 'flex', flexDirection: 'column', gap: 24, boxShadow: 'var(--shadow-lg)',
            textAlign: 'left'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <h2 style={{ fontSize: '20px', fontWeight: 800, marginBottom: 4, marginTop: 0 }}>Ficha y Edición de Remito</h2>
                <span style={{ fontSize: '13px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  Transacción ID: {editingRemito.transaccion_id}
                </span>
              </div>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => setShowEditModal(false)}
                style={{ minWidth: 'auto', padding: '4px 10px', border: '1px solid var(--border)' }}
              >
                X
              </button>
            </div>

            <form onSubmit={handleSaveEdit} style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              {/* Información Fija */}
              <div style={{
                background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border)',
                borderRadius: '12px', padding: '16px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, fontSize: '13px'
              }}>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Comprobante:</span>
                  <div style={{ fontWeight: 600, marginTop: 2 }}>{editingRemito.numero}</div>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Fecha Emisión:</span>
                  <div style={{ fontWeight: 600, marginTop: 2 }}>{editingRemito.fecha}</div>
                </div>
                <div style={{ gridColumn: '1 / -1' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Cliente:</span>
                  <div style={{ fontWeight: 600, marginTop: 2 }}>{editingRemito.cliente}</div>
                </div>
              </div>

              {/* Checkboxes de Firmas */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <h4 style={{ fontSize: '13.5px', fontWeight: 700, margin: 0, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.03em' }}>Confirmación de Firmas</h4>
                <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', fontSize: '14px' }}>
                  <input
                    type="checkbox"
                    checked={!!editingRemito.confirmado_cliente}
                    onChange={(e) => setEditingRemito(prev => ({ ...prev, confirmado_cliente: e.target.checked }))}
                    style={{ cursor: 'pointer', width: '16px', height: '16px' }}
                  />
                  <span>Firma OL (Confirmado por Cliente)</span>
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', fontSize: '14px' }}>
                  <input
                    type="checkbox"
                    checked={!!editingRemito.confirmado_distribuidor}
                    onChange={(e) => setEditingRemito(prev => ({ ...prev, confirmado_distribuidor: e.target.checked }))}
                    style={{ cursor: 'pointer', width: '16px', height: '16px' }}
                  />
                  <span>Firma Distribuidor (Conformidad)</span>
                </label>
              </div>

              {/* Checkboxes de Ejemplares Escaneados */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <h4 style={{ fontSize: '13.5px', fontWeight: 700, margin: 0, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.03em' }}>Ejemplares Digitalizados</h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: '13.5px' }}>
                    <input
                      type="checkbox"
                      checked={!!editingRemito.copias_escaneadas?.original}
                      onChange={(e) => setEditingRemito(prev => ({
                        ...prev,
                        copias_escaneadas: { ...prev.copias_escaneadas, original: e.target.checked },
                        ocr_original: e.target.checked ? "{}" : null
                      }))}
                      style={{ cursor: 'pointer' }}
                    />
                    <span>Original</span>
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: '13.5px' }}>
                    <input
                      type="checkbox"
                      checked={!!editingRemito.copias_escaneadas?.duplicado}
                      onChange={(e) => setEditingRemito(prev => ({
                        ...prev,
                        copias_escaneadas: { ...prev.copias_escaneadas, duplicado: e.target.checked },
                        ocr_duplicado: e.target.checked ? "{}" : null
                      }))}
                      style={{ cursor: 'pointer' }}
                    />
                    <span>Duplicado</span>
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: '13.5px' }}>
                    <input
                      type="checkbox"
                      checked={!!editingRemito.copias_escaneadas?.triplicado}
                      onChange={(e) => setEditingRemito(prev => ({
                        ...prev,
                        copias_escaneadas: { ...prev.copias_escaneadas, triplicado: e.target.checked },
                        ocr_triplicado: e.target.checked ? "{}" : null
                      }))}
                      style={{ cursor: 'pointer' }}
                    />
                    <span>Triplicado</span>
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: '13.5px' }}>
                    <input
                      type="checkbox"
                      checked={!!editingRemito.copias_escaneadas?.cuatriplicado}
                      onChange={(e) => setEditingRemito(prev => ({
                        ...prev,
                        copias_escaneadas: { ...prev.copias_escaneadas, cuatriplicado: e.target.checked },
                        ocr_cuatriplcado: e.target.checked ? "{}" : null
                      }))}
                      style={{ cursor: 'pointer' }}
                    />
                    <span>Cuatriplicado</span>
                  </label>
                </div>
              </div>

              {/* Estado de Reclamo */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <h4 style={{ fontSize: '13.5px', fontWeight: 700, margin: 0, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.03em' }}>Reclamos y Auditoría</h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, alignItems: 'center' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', fontSize: '14px' }}>
                    <input
                      type="checkbox"
                      checked={!!editingRemito.reclamado}
                      onChange={(e) => {
                        const isChecked = e.target.checked;
                        const today = new Date().toISOString().split('T')[0];
                        setEditingRemito(prev => ({
                          ...prev,
                          reclamado: isChecked,
                          finne_Reclamado: isChecked ? 1 : 0,
                          finne_FechaUltimoReclamo: isChecked ? today : ''
                        }));
                      }}
                      style={{ cursor: 'pointer', width: '16px', height: '16px' }}
                    />
                    <span>Marcar como Reclamado</span>
                  </label>
                  {!!editingRemito.reclamado && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Fecha de Reclamo:</span>
                      <input
                        type="date"
                        value={editingRemito.fecha_ultimo_reclamo || ''}
                        onChange={(e) => setEditingRemito(prev => ({ ...prev, fecha_ultimo_reclamo: e.target.value, finne_FechaUltimoReclamo: e.target.value }))}
                        style={{
                          background: 'var(--surface-hover)', border: '1px solid var(--border)',
                          color: 'var(--text)', padding: '6px 10px', borderRadius: '6px', fontSize: '13px'
                        }}
                      />
                    </div>
                  )}
                </div>
              </div>

              {/* Botones de control */}
              <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end', marginTop: 12 }}>
                <button
                  type="button"
                  onClick={() => setShowEditModal(false)}
                  className="btn btn-secondary btn-md"
                  style={{ border: '1px solid var(--border)' }}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="btn btn-primary btn-md"
                >
                  Guardar Cambios
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
 
      {/* MODAL DE CONFIRMACIÓN DE SINCRONIZACIÓN DE FINNEGANS */}
      {showSyncConfirmModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, width: '100%', height: '100%',
          background: 'rgba(15, 23, 42, 0.85)', display: 'flex', alignItems: 'center',
          justifyContent: 'center', zIndex: 10000, padding: '24px', backdropFilter: 'blur(12px)'
        }}>
          <div className="glass" style={{
            width: '100%', maxWidth: '460px', padding: '36px', borderRadius: '24px',
            display: 'flex', flexDirection: 'column', gap: 24, boxShadow: 'var(--shadow-lg)',
            textAlign: 'center'
          }}>
            <div>
              <h2 style={{ fontSize: '20px', fontWeight: 800, marginBottom: 8, marginTop: 0 }}>¿Iniciar Sincronización Manual?</h2>
              <p style={{ fontSize: '14.5px', color: 'var(--text-muted)', lineHeight: 1.5, margin: 0 }}>
                Este proceso conecta a Finnegans ERP y descarga los nuevos remitos facturados. Dado que <strong>puede demorar varios minutos</strong>, y el sistema ya lo ejecuta automáticamente de fondo por cron diariamente, ¿desea continuarlo de todas formas?
              </p>
            </div>

            <div style={{ display: 'flex', gap: 16, justifyContent: 'center' }}>
              <button
                type="button"
                onClick={() => setShowSyncConfirmModal(false)}
                className="btn btn-secondary btn-md"
                style={{ flexGrow: 1, border: '1px solid var(--border)' }}
              >
                No, Cancelar
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowSyncConfirmModal(false);
                  handleAction('sync-finnegans', 'Sincronizar Finnegans');
                }}
                className="btn btn-primary btn-md"
                style={{ flexGrow: 1 }}
              >
                Sí, Actualizar
              </button>
            </div>
          </div>
        </div>
      )}





      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        .spin-animation {
          animation: spin 1.5s linear infinite;
        }
        @keyframes shimmer {
          0% { left: -45%; }
          100% { left: 100%; }
        }
        .shimmer-progress-bar {
          background: linear-gradient(90deg, transparent, var(--primary), transparent);
          border-radius: 4px;
        }
        .selected-row {
          background-color: var(--surface-hover) !important;
        }
        .tab-navigation button {
          transition: all 0.3s ease;
        }
      `}</style>
    </div>
  );
}

export default App;
