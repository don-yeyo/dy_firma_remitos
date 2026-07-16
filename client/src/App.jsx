import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useAuth } from './config/AuthContext';
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
  Clock
} from 'lucide-react';

function App() {
  const { isAuthenticated, user, loginMicrosoft, logout } = useAuth();
  
  // URL del backend local (configurable dinámicamente)
  const [apiUrl, setApiUrl] = useState(() => {
    return localStorage.getItem('dy_remitos_api_url') || 'http://localhost:8000';
  });
  const [isConfigOpen, setIsConfigOpen] = useState(false);
  const [tempApiUrl, setTempApiUrl] = useState(apiUrl);

  // Estados del Dashboard
  const [status, setStatus] = useState('idle');
  const [logs, setLogs] = useState([]);
  const [history, setHistory] = useState([]);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [backendConfig, setBackendConfig] = useState(null);

  const consoleEndRef = useRef(null);

  // Guardar la URL configurada por el usuario
  const saveApiConfig = (e) => {
    e.preventDefault();
    const formattedUrl = tempApiUrl.replace(/\/$/, ''); // Remover barra final
    setApiUrl(formattedUrl);
    localStorage.setItem('dy_remitos_api_url', formattedUrl);
    setIsConfigOpen(false);
    showTempLog(`[SYSTEM] URL del servidor actualizada a: ${formattedUrl}`);
  };

  const showTempLog = (msg) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, `[${timestamp}] ${msg}`]);
  };

  // Polling de Status y Logs (cada 2.0 segundos)
  useEffect(() => {
    if (!isAuthenticated) return;

    const fetchStatus = async () => {
      try {
        const res = await axios.get(`${apiUrl}/api/status`);
        setStatus(res.data.status);
        setLogs(res.data.logs);
      } catch (err) {
        // No alarmar de inmediato en consola, pero reportar pérdida de enlace si persiste
      }
    };

    fetchStatus(); // Primer llamado inmediato
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, [isAuthenticated, apiUrl]);

  // Cargar Historial de Remitos
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

  // Cargar Configuración del Servidor
  const fetchBackendConfig = async () => {
    try {
      const res = await axios.get(`${apiUrl}/api/config`);
      setBackendConfig(res.data);
    } catch (err) {
      setBackendConfig(null);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchHistory();
      fetchBackendConfig();
    }
  }, [isAuthenticated, apiUrl]);

  // Hacer scroll automático al final de la consola cuando entran nuevos logs
  useEffect(() => {
    if (consoleEndRef.current) {
      consoleEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  // Disparar las acciones del bot
  const handleAction = async (endpoint, actionName) => {
    try {
      showTempLog(`[CLIENT] Enviando orden para: "${actionName}"...`);
      const res = await axios.post(`${apiUrl}/api/${endpoint}`);
      if (res.data.status === 'started') {
        showTempLog(`[SERVER] ${res.data.message}`);
        setStatus(endpoint === 'scan-and-process' ? 'scanning-and-processing' : 
                  endpoint === 'scan' ? 'scanning' : 
                  endpoint === 'process' ? 'processing' : 'syncing');
      } else {
        showTempLog(`[SERVER ERROR] ${res.data.message}`);
      }
    } catch (err) {
      showTempLog(`[CLIENT ERROR] No se pudo conectar al servidor local en ${apiUrl}. Verifique que el servicio esté corriendo en la red local.`);
    }
  };

  // Limpiar logs en pantalla
  const handleClearLogs = async () => {
    try {
      await axios.post(`${apiUrl}/api/clear-logs`);
      setLogs([]);
    } catch (err) {
      setLogs([]);
    }
  };

  // --- VISTA DE LOGIN ---
  if (!isAuthenticated) {
    return (
      <div className="login-wrapper">
        <div className="login-card glass-container">
          <div className="login-brand">
            <div className="login-logo">R</div>
            <h2>Don Yeyo S.A.</h2>
            <p>Auditoría de Recepción y Firma de Remitos<br />Acceso exclusivo para personal autorizado</p>
          </div>
          
          <button className="btn-microsoft-login" onClick={loginMicrosoft}>
            {/* SVG del Logo de Microsoft */}
            <svg viewBox="0 0 23 23">
              <path fill="#f3f2f1" d="M1 1h10v10H1z"/>
              <path fill="#f3f2f1" d="M12 1h10v10H12z"/>
              <path fill="#f3f2f1" d="M1 12h10v10H1z"/>
              <path fill="#f3f2f1" d="M12 12h10v10H12z"/>
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
      <header className="app-header">
        <div className="brand-section">
          <div className="brand-logo">R</div>
          <div className="brand-title">
            <h1>Firma de Remitos</h1>
            <p>Don Yeyo S.A.</p>
          </div>
        </div>

        <div className="user-profile">
          <div className="user-info">
            <div className="user-name">{user?.name}</div>
            <div className="user-email">{user?.email}</div>
          </div>
          
          <button 
            className="btn-logout" 
            style={{ padding: '8px 12px' }}
            onClick={() => setIsConfigOpen(!isConfigOpen)}
            title="Configurar Conexión API"
          >
            <Settings size={16} />
          </button>

          <button className="btn-logout" onClick={logout}>
            <LogOut size={16} />
            Salir
          </button>
        </div>
      </header>

      {/* Modal / Panel de Configuración de IP */}
      {isConfigOpen && (
        <div style={{
          position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
          background: 'rgba(15, 23, 42, 0.8)', display: 'flex', alignItems: 'center',
          justifyContent: 'center', zIndex: 1000, padding: '20px'
        }}>
          <form onSubmit={saveApiConfig} className="glass-container" style={{
            width: '100%', maxWidth: '400px', padding: '30px', display: 'flex',
            flexDirection: 'column', gap: 20
          }}>
            <h3 style={{ fontSize: '18px', fontWeight: 700 }}>Configuración de Red LAN</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <label style={{ fontSize: '13px', color: 'var(--text-muted)' }}>URL del Servidor Backend local:</label>
              <input 
                type="text" 
                value={tempApiUrl} 
                onChange={(e) => setTempApiUrl(e.target.value)}
                style={{
                  background: 'rgba(0, 0, 0, 0.4)', border: '1px solid var(--glass-border)',
                  color: 'white', padding: '12px', borderRadius: '8px', fontSize: '14px',
                  fontFamily: 'var(--font-mono)'
                }}
              />
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                Ejemplo: http://192.168.1.100:8000 o http://localhost:8000
              </span>
            </div>
            
            <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end', marginTop: 10 }}>
              <button 
                type="button" 
                onClick={() => setIsConfigOpen(false)}
                className="btn-logout"
              >
                Cancelar
              </button>
              <button 
                type="submit" 
                className="btn-logout"
                style={{ background: 'var(--accent-gradient)', border: 'none', fontWeight: 600 }}
              >
                Guardar
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Widget de Estado Actual */}
      <section className="status-widget glass-container">
        <div className="status-info">
          <div className={`status-badge ${status === 'idle' ? 'idle' : 'busy'}`}>
            {status === 'idle' ? (
              <>
                <CheckCircle size={14} /> Listo
              </>
            ) : (
              <>
                <Loader size={14} className="spin-animation" style={{ animation: 'spin 1.5s linear infinite' }} /> {status}
              </>
            )}
          </div>
          <div>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Servicio local en:</span>
            <div style={{ fontSize: '14px', fontWeight: 500, fontFamily: 'var(--font-mono)' }}>{apiUrl}</div>
          </div>
        </div>

        {backendConfig && (
          <div style={{ textAlign: 'right', fontSize: '12px', color: 'var(--text-muted)' }}>
            <div>Escáner: <strong style={{ color: 'white' }}>{backendConfig.SCANNER_NAME}</strong></div>
            <div>Origen: <strong style={{ color: 'white' }}>{backendConfig.SCAN_SOURCE} ({backendConfig.SCAN_DPI} DPI)</strong></div>
          </div>
        )}
      </section>

      {/* Grid Principal: Botones de Acción + Terminal de Logs */}
      <main className="dashboard-grid">
        {/* Lado Izquierdo: Botones de Acciones */}
        <section className="actions-section">
          {/* Acción Principal: Flujo Completo */}
          <div 
            className="action-card glass-container primary-flow"
            onClick={() => handleAction('scan-and-process', 'Escanear + Procesar Todo')}
          >
            <div className="action-icon">
              <Play size={24} />
            </div>
            <div>
              <h3>Escanear + Procesar Todo</h3>
              <p>Escanea masivamente los remitos de la bandeja superior de la Ricoh e inicia el análisis automático por IA para firmar en base de datos y SharePoint en un solo clic.</p>
            </div>
          </div>

          {/* Paso 1: Escaneo */}
          <div 
            className="action-card glass-container"
            onClick={() => handleAction('scan', 'Escaneo Masivo (Paso 1)')}
          >
            <div className="action-icon">
              <Printer size={20} />
            </div>
            <div>
              <h3>Escaneo Masivo</h3>
              <p>Paso 1: Jala los papeles de la bandeja y los guarda localmente como imágenes JPG.</p>
            </div>
          </div>

          {/* Paso 2: Procesar IA */}
          <div 
            className="action-card glass-container"
            onClick={() => handleAction('process', 'Procesar Imágenes (Paso 2)')}
          >
            <div className="action-icon">
              <Cpu size={20} />
            </div>
            <div>
              <h3>Procesar por IA</h3>
              <p>Paso 2: Lee las imágenes escaneadas de la carpeta local y busca firmas/sellos con AI Builder.</p>
            </div>
          </div>

          {/* Finnegans Sync */}
          <div 
            className="action-card glass-container"
            style={{ gridColumn: '1 / -1' }}
            onClick={() => handleAction('sync-finnegans', 'Sincronizar Finnegans')}
          >
            <div className="action-icon">
              <RefreshCw size={20} />
            </div>
            <div>
              <h3>Sincronizar con Finnegans ERP</h3>
              <p>Conecta a la API de Finnegans para descargar y registrar los nuevos remitos facturados en la base de datos de auditoría de AWS MySQL.</p>
            </div>
          </div>
        </section>

        {/* Lado Derecho: Consola de Logs */}
        <section className="console-section glass-container">
          <div className="console-header">
            <div className="console-title">
              <TerminalIcon size={16} /> Consola en tiempo real
            </div>
            <div className="console-controls">
              <button className="btn-clear" onClick={handleClearLogs}>
                Limpiar Pantalla
              </button>
            </div>
          </div>
          <div className="console-body">
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
        </section>
      </main>

      {/* Historial de Auditoría */}
      <section className="history-section glass-container">
        <div className="history-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Clock size={20} className="text-muted" />
            <h2>Historial de Auditoría Reciente</h2>
          </div>
          <button className="btn-logout" onClick={fetchHistory} disabled={isHistoryLoading}>
            <RefreshCw size={14} className={isHistoryLoading ? 'spin-animation' : ''} style={{ animation: isHistoryLoading ? 'spin 1.5s linear infinite' : 'none' }} />
            Actualizar
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

      {/* Agregar un estilo de rotación clave en css */}
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
