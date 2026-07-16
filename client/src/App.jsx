import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useAuth } from './config/AuthContext';
import packageJson from '../package.json';
import { 
  Play, 
  Cpu, 
  RefreshCw, 
  Printer, 
  Terminal as TerminalIcon, 
  LogOut, 
  Settings, 
  CheckCircle, 
  XCircle,
  Loader,
  Clock,
  Sun,
  Moon,
  ChevronDown,
  ChevronUp,
  Info,
  Share2
} from 'lucide-react';

const appVersion = packageJson.version || '1.0.0';

// Helper para traducir e interpretar logs complejos en textos limpios y comprensibles para el usuario
const getFriendlyProgressMessage = (status, lastLogLine) => {
  if (!lastLogLine) {
    if (status === 'scanning') return 'Inicializando alimentador Ricoh...';
    if (status === 'processing') return 'Preparando motor de Inteligencia Artificial...';
    if (status === 'scanning-and-processing') return 'Iniciando flujo de escaneo masivo...';
    if (status === 'syncing') return 'Conectando al servidor del ERP Finnegans...';
    return 'Procesando...';
  }
  
  const text = lastLogLine.toLowerCase();
  
  if (status === 'scanning' || status === 'scanning-and-processing') {
    if (text.includes("estableciendo conexión") || text.includes("conexión establecida") || text.includes("conectando")) {
      return "Estableciendo enlace de red con la Ricoh IM C300...";
    }
    if (text.includes("escaneando página")) {
      const match = lastLogLine.match(/página\s*(\d+)/i);
      return match ? `Escaneando remito físico en papel (Página ${match[1]})...` : "Escaneando remitos desde la bandeja superior...";
    }
    if (text.includes("esperando") && text.includes("transición")) {
      return "Acomodando rodillo de arrastre y posicionando siguiente hoja...";
    }
    if (text.includes("guardada") || text.includes("procesada") || text.includes("convertida")) {
      return "Guardando archivo digitalizado en el servidor local...";
    }
    if (text.includes("se ha quedado sin páginas") || text.includes("finalizado")) {
      return "Alimentador vacío. Finalizando escaneo...";
    }
  }
  
  if (status === 'processing' || status === 'scanning-and-processing') {
    if (text.includes("enviando datos") || text.includes("procesando imagen") || text.includes("enviando al flujo")) {
      return "Interpretando remito y buscando firmas/sellos con IA...";
    }
    if (text.includes("actualizando") || text.includes("conectando a bd") || text.includes("persistencia")) {
      return "Guardando resultados de auditoría en base de datos central...";
    }
    if (text.includes("exitosamente") || text.includes("✔ [bd]")) {
      return "Guardando resultados y archivando en SharePoint...";
    }
  }

  if (status === 'syncing') {
    if (text.includes("api de finnegans") || text.includes("descargando") || text.includes("reporte")) {
      return "Conectando al ERP y descargando nuevos remitos facturados...";
    }
    if (text.includes("actualizando") || text.includes("insertando") || text.includes("bd")) {
      return "Registrando nuevos remitos en la base de datos de auditoría...";
    }
  }
  
  // Mensaje por defecto simplificado (removiendo timestamp [10:30:15])
  return lastLogLine.replace(/^\[.*?\]\s*/, "");
};

// Helper para parsear estadisticas a partir de las lineas de logs acumuladas en la corrida
const parseLogSummary = (logLines) => {
  let escaneados = 0;
  let exitososIa = 0;
  let fallidosIa = 0;
  let bdActualizados = 0;
  let bdNoEncontrados = 0;

  logLines.forEach(line => {
    // Escaneo
    if (line.includes("guardada en:") || line.includes("guardada directamente") || line.includes("procesada y guardada")) {
      escaneados++;
    }
    // Procesamiento IA
    if (line.includes("Procesado exitosamente")) {
      exitososIa++;
    }
    if (line.includes("Error durante el análisis") || line.includes("Excepción en procesamiento")) {
      fallidosIa++;
    }
    // Base de Datos
    if (line.includes("Base de Datos actualizada con éxito") || line.includes("✔ [BD]")) {
      bdActualizados++;
    }
    if (line.includes("No se encontró ningún registro") || line.includes("❌ No se encontró en DB")) {
      bdNoEncontrados++;
    }
  });

  // Intentar leer el total de paginas reportadas por el ADF
  const scanMatch = logLines.join("\n").match(/Total de páginas escaneadas:\s*(\d+)/i);
  if (scanMatch) {
    escaneados = parseInt(scanMatch[1], 10);
  }

  return {
    escaneados,
    exitososIa,
    fallidosIa,
    bdActualizados,
    bdNoEncontrados
  };
};

function App() {
  const { isAuthenticated, user, loginMicrosoft, logout } = useAuth();
  
  // URL de la API local
  const [apiUrl, setApiUrl] = useState(() => {
    return localStorage.getItem('dy_remitos_api_url') || 'http://localhost:8000';
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

  // Estados del Dashboard
  const [status, setStatus] = useState('idle');
  const [logs, setLogs] = useState([]);
  const [history, setHistory] = useState([]);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);

  // Estados de control de consolas y modales
  const [showConsole, setShowConsole] = useState(false); // Consola técnica oculta por defecto
  const [showModal, setShowModal] = useState(false); // Modal de progreso
  const [actionStarted, setActionStarted] = useState(false); // Indica si iniciamos un proceso
  const [summaryData, setSummaryData] = useState(null); // Estadisticas del modal final

  const consoleEndRef = useRef(null);

  const saveApiConfig = (e) => {
    e.preventDefault();
    const formattedUrl = tempApiUrl.replace(/\/$/, '');
    setApiUrl(formattedUrl);
    localStorage.setItem('dy_remitos_api_url', formattedUrl);
    setIsConfigOpen(false);
    showTempLog(`[SYSTEM] Dirección IP de red LAN actualizada a: ${formattedUrl}`);
  };

  const showTempLog = (msg) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, `[${timestamp}] ${msg}`]);
  };

  // Polling adaptativo
  useEffect(() => {
    if (!isAuthenticated) return;

    const fetchStatus = async () => {
      try {
        const res = await axios.get(`${apiUrl}/api/status`);
        setStatus(res.data.status);
        setLogs(res.data.logs);
      } catch (err) {
        // Enlace offline
      }
    };

    fetchStatus();

    // Polling rápido a 2 segundos si hay un proceso corriendo, sino se relaja a 15 segundos
    const pollingTime = status === 'idle' ? 15000 : 2000;
    const interval = setInterval(fetchStatus, pollingTime);
    
    return () => clearInterval(interval);
  }, [isAuthenticated, apiUrl, status]);

  // Si se inició una acción en el cliente y el status cambió a busy, abrir el modal de progreso
  useEffect(() => {
    if (status !== 'idle') {
      setShowModal(true);
      setActionStarted(true);
      setSummaryData(null); // Limpiar resumen anterior
    } else if (status === 'idle' && actionStarted) {
      // El servidor terminó el trabajo de fondo y volvió a reposo. Armar resumen final.
      setSummaryData(parseLogSummary(logs));
      fetchHistory(); // Recargar historial automáticamente
    }
  }, [status, actionStarted]);

  // Cargar Historial
  const fetchHistory = async () => {
    if (!isAuthenticated) return;
    setIsHistoryLoading(true);
    try {
      const res = await axios.get(`${apiUrl}/api/history`);
      if (Array.isArray(res.data)) {
        setHistory(res.data);
      }
    } catch (err) {
      console.error("Error al traer historial:", err);
    } finally {
      setIsHistoryLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchHistory();
    }
  }, [isAuthenticated, apiUrl]);

  // Auto-scroll de logs solo si hay procesos activos
  useEffect(() => {
    if (status !== 'idle' && consoleEndRef.current) {
      consoleEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, status]);

  const handleAction = async (endpoint, actionName) => {
    try {
      showTempLog(`[CLIENT] Iniciando: "${actionName}"...`);
      setStatus(endpoint === 'scan-and-process' ? 'scanning-and-processing' : 
                endpoint === 'scan' ? 'scanning' : 
                endpoint === 'process' ? 'processing' : 'syncing');
      
      const res = await axios.post(`${apiUrl}/api/${endpoint}`);
      if (res.data.status === 'started') {
        showTempLog(`[SERVER] ${res.data.message}`);
      } else {
        showTempLog(`[SERVER ERROR] ${res.data.message}`);
        setStatus('idle');
      }
    } catch (err) {
      showTempLog(`[CLIENT ERROR] Sin conexión con el servidor en ${apiUrl}. Verifique que el .exe esté ejecutado en la notebook local.`);
      setStatus('idle');
    }
  };

  const handleClearLogs = async () => {
    try {
      await axios.post(`${apiUrl}/api/clear-logs`);
      setLogs([]);
    } catch (err) {
      setLogs([]);
    }
  };

  const handleShareLogs = async () => {
    const logsText = logs.join('\n');
    if (!logsText) {
      showTempLog('[CLIENT] No hay logs para compartir.');
      return;
    }
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Logs de Auditoría de Remitos - Don Yeyo S.A.',
          text: logsText
        });
      } catch (err) {
        // Ignorar cancelaciones
      }
    } else {
      try {
        await navigator.clipboard.writeText(logsText);
        showTempLog('[CLIENT] Logs copiados al portapapeles.');
        alert('Logs copiados al portapapeles.');
      } catch (err) {
        showTempLog('[CLIENT] Error al copiar logs al portapapeles.');
      }
    }
  };

  // Cerrar el modal final y desplegar la consola técnica de logs en el Dashboard
  const closeSummaryModal = () => {
    setShowModal(false);
    setActionStarted(false);
    setSummaryData(null);
    setShowConsole(true); // Desplegar logs detallados al finalizar
  };

  const getCleanLastLogLine = () => {
    if (logs.length === 0) return null;
    return logs[logs.length - 1];
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
              <path fill="#f3f2f1" d="M1 1h10v10H1z"/>
              <path fill="#f3f2f1" d="M12 1h10v10H12z"/>
              <path fill="#1 12h10v10H1z"/>
              <path fill="#12 12h10v10H12z"/>
              <path fill="#f25022" d="M1 1h10v10H1z"/>
              <path fill="#7fba00" d="M12 1h10v10H12z"/>
              <path fill="#00a4ef" d="M1 12h10v10H1z"/>
              <path fill="#ffb900" d="M12 12h10v10H12z"/>
            </svg>
            Iniciar Sesión con Microsoft
          </button>
        </div>
      </div>
    );
  }

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
          <div className="user-info desktop-only">
            <div className="user-name">{user?.name}</div>
            <div className="user-email">{user?.email}</div>
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
          position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
          background: 'rgba(15, 23, 42, 0.75)', display: 'flex', alignItems: 'center',
          justifyContent: 'center', zIndex: 1000, padding: '20px'
        }}>
          <form onSubmit={saveApiConfig} className="glass" style={{
            width: '100%', maxWidth: '400px', padding: '30px', display: 'flex',
            flexDirection: 'column', gap: 20, borderRadius: 'var(--radius)'
          }}>
            <h3 style={{ fontSize: '18px', fontWeight: 700 }}>Configuración de Red LAN</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <label style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Dirección IP de la notebook (Servidor):</label>
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
                Escribí la dirección que se muestra en la pantalla del .exe (ej: http://192.168.1.100:8000)
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

      {/* MODAL DE PROGRESO Y RESUMEN A PANTALLA COMPLETA (GLASS) */}
      {showModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
          background: 'rgba(15, 23, 42, 0.85)', display: 'flex', alignItems: 'center',
          justifyContent: 'center', zIndex: 900, padding: '24px', backdropFilter: 'blur(12px)'
        }}>
          <div className="glass" style={{
            width: '100%', maxWidth: '480px', padding: '36px', borderRadius: '24px',
            textAlign: 'center', display: 'flex', flexDirection: 'column', gap: 24,
            boxShadow: 'var(--shadow-lg)'
          }}>
            {!summaryData ? (
              // --- VISTA 1: PROCESANDO ---
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
                  <p style={{ fontSize: '14px', color: 'var(--text)', fontWeight: 500, minHeight: '40px' }}>
                    {getFriendlyProgressMessage(status, getCleanLastLogLine())}
                  </p>
                </div>
                <div style={{ background: 'rgba(0, 0, 0, 0.2)', padding: '14px', borderRadius: '12px', textAlign: 'left' }}>
                  <div style={{ fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: 4 }}>Evento técnico en caliente:</div>
                  <div style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: '#34d399', wordBreak: 'break-all' }}>
                    {getCleanLastLogLine() || 'Estableciendo enlace de comunicación...'}
                  </div>
                </div>
              </>
            ) : (
              // --- VISTA 2: RESUMEN FINAL ---
              <>
                <div style={{ display: 'flex', justifyContent: 'center', color: 'var(--success)' }}>
                  <CheckCircle size={58} />
                </div>
                <div>
                  <h2 style={{ fontSize: '22px', fontWeight: 800, marginBottom: 4 }}>Proceso Finalizado</h2>
                </div>
                
                {/* Cuadro de Estadisticas */}
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
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', fontSize: '13.5px' }}>
                    <span style={{ textAlign: 'left', color: 'var(--text-muted)' }}>Páginas escaneadas:</span>
                    <strong style={{ textAlign: 'right', color: 'var(--text)' }}>{summaryData.escaneados}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', fontSize: '13.5px' }}>
                    <span style={{ textAlign: 'left', color: 'var(--text-muted)' }}>Remitos analizados por IA (OK):</span>
                    <strong style={{ textAlign: 'right', color: 'var(--success)' }}>{summaryData.exitosasIa}</strong>
                  </div>
                  {summaryData.fallidosIa > 0 && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', fontSize: '13.5px', color: 'var(--error)' }}>
                      <span style={{ textAlign: 'left' }}>Análisis IA fallidos:</span>
                      <strong style={{ textAlign: 'right' }}>{summaryData.fallidosIa}</strong>
                    </div>
                  )}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', fontSize: '13.5px' }}>
                    <span style={{ textAlign: 'left', color: 'var(--text-muted)' }}>Registros guardados en BD:</span>
                    <strong style={{ textAlign: 'right', color: 'var(--primary)' }}>{summaryData.bdActualizados}</strong>
                  </div>
                  {summaryData.bdNoEncontrados > 0 && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', fontSize: '13.5px', color: 'var(--warning)' }}>
                      <span style={{ textAlign: 'left' }}>No encontrados en BD (sin ERP):</span>
                      <strong style={{ textAlign: 'right' }}>{summaryData.bdNoEncontrados}</strong>
                    </div>
                  )}
                </div>

                <button 
                  onClick={closeSummaryModal} 
                  className="btn btn-primary btn-md"
                  style={{ width: '100%' }}
                >
                  Cerrar y Ver Detalles
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {/* Grid de Acciones */}
      <main className="actions-section">
        {/* Flujo Completo */}
        <div 
          className="action-card glass full-width"
          onClick={() => handleAction('scan-and-process', 'Escanear + Procesar Todo')}
        >
          <div className="action-icon">
            <Play size={20} />
          </div>
          <div>
            <h3>Escanear + Procesar Todo</h3>
            <p>Jala los remitos del alimentador de la Ricoh, los digitaliza e inicia el análisis automático por IA para firmar en base de datos y SharePoint en un solo paso.</p>
          </div>
        </div>

        {/* Paso 1: Escaneo */}
        <div 
          className="action-card glass"
          onClick={() => handleAction('scan', 'Escaneo Masivo (Paso 1)')}
        >
          <div className="action-icon">
            <Printer size={18} />
          </div>
          <div>
            <h3>Escaneo Masivo</h3>
            <p>Paso 1: Jala los papeles de la bandeja física del escáner y los almacena en formato JPG.</p>
          </div>
        </div>

        {/* Paso 2: Procesar IA */}
        <div 
          className="action-card glass"
          onClick={() => handleAction('process', 'Procesar Imágenes (Paso 2)')}
        >
          <div className="action-icon">
            <Cpu size={18} />
          </div>
          <div>
            <h3>Procesar por IA</h3>
            <p>Paso 2: Analiza las imágenes digitalizadas en busca de firmas y sellos con AI Builder.</p>
          </div>
        </div>

        {/* Finnegans Sync */}
        <div 
          className="action-card glass"
          style={{ gridColumn: '1 / -1' }}
          onClick={() => handleAction('sync-finnegans', 'Sincronizar Finnegans')}
        >
          <div className="action-icon">
            <RefreshCw size={18} />
          </div>
          <div>
            <h3>Actualizar remitos desde ERP</h3>
            <p>Sincroniza y descarga los nuevos remitos facturados en Finnegans a la base de datos de auditoría. Este proceso también se ejecuta de forma automática todos los días de fondo en el servidor.</p>
          </div>
        </div>
      </main>

      {/* Sección Desplegable de Consola Técnica */}
      <section className="console-section glass">
        <div 
          className="console-header" 
          style={{ cursor: 'pointer', userSelect: 'none' }}
          onClick={() => setShowConsole(!showConsole)}
        >
          <div className="console-title">
            <TerminalIcon size={14} /> Consola
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            {showConsole ? <ChevronUp size={14} className="text-muted" /> : <ChevronDown size={14} className="text-muted" />}
          </div>
        </div>
        {showConsole && (
          <>
            <div className="console-body" style={{ height: '300px' }}>
              {logs.length === 0 ? (
                <div className="console-line" style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>
                  Esperando eventos o acciones...
                </div>
              ) : (
                logs.map((log, idx) => (
                  <div key={idx} className="console-line">
                    {log}
                  </div>
                ))
              )}
              <div ref={consoleEndRef} />
            </div>
            <div style={{ background: '#090d16', padding: '10px 20px', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <button 
                className="btn btn-secondary btn-sm" 
                style={{ padding: '4px 12px', fontSize: '11px' }} 
                onClick={handleShareLogs}
                title="Compartir o copiar logs técnicos"
              >
                <Share2 size={11} /> Compartir logs
              </button>
              <button 
                className="btn btn-secondary btn-sm" 
                style={{ padding: '4px 12px', fontSize: '11px' }} 
                onClick={handleClearLogs}
              >
                Limpiar logs
              </button>
            </div>
          </>
        )}
      </section>

      {/* Historial */}
      <section className="history-section glass">
        <div className="history-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Clock size={18} className="text-muted" />
            <h2>Historial</h2>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={fetchHistory} disabled={isHistoryLoading}>
            <RefreshCw size={12} className={isHistoryLoading ? 'spin-animation' : ''} style={{ animation: isHistoryLoading ? 'spin 1.5s linear infinite' : 'none' }} />
            &nbsp;Actualizar
          </button>
        </div>

        <div className="history-table-wrapper">
          <table className="history-table">
            <thead>
              <tr>
                <th>Transacción ID</th>
                <th>Número de Remito</th>
                <th>Fecha Emisión</th>
                <th>Ejemplares Digitalizados</th>
                <th>Firma Operador (OL)</th>
                <th>Firma Distribuidor</th>
              </tr>
            </thead>
            <tbody>
              {history.length === 0 ? (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '30px' }}>
                    No hay registros en el historial o el servidor está inaccesible.
                  </td>
                </tr>
              ) : (
                history.map((row) => (
                  <tr key={row.transaccion_id}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{row.transaccion_id}</td>
                    <td>{row.numero}</td>
                    <td>{row.fecha}</td>
                    <td>
                      <div className="copia-indicators">
                        <span className={`copia-dot ${row.copias_escaneadas.original ? 'present' : 'absent'}`}>O</span>
                        <span className={`copia-dot ${row.copias_escaneadas.duplicado ? 'present' : 'absent'}`}>D</span>
                        <span className={`copia-dot ${row.copias_escaneadas.triplicado ? 'present' : 'absent'}`}>T</span>
                        <span className={`copia-dot ${row.copias_escaneadas.cuatriplicado ? 'present' : 'absent'}`}>C</span>
                      </div>
                    </td>
                    <td>
                      {row.copias === 2 ? (
                        <span className="badge-verification not-required">no req.</span>
                      ) : (
                        <span className={`badge-verification ${row.confirmado_cliente ? 'verified' : 'pending'}`}>
                          {row.confirmado_cliente ? 'Sí' : 'No'}
                        </span>
                      )}
                    </td>
                    <td>
                      <span className={`badge-verification ${row.confirmado_distribuidor ? 'verified' : 'pending'}`}>
                        {row.confirmado_distribuidor ? 'Sí' : 'No'}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default App;
