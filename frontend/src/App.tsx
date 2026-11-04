import { useEffect, useState } from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import {
  Activity,
  ShieldCheck,
  LayoutDashboard,
  Cpu,
  Radio,
  KeyRound,
  FileCheck2,
  Gauge,
  Siren,
  Network,
  FlaskConical,
  ChartNoAxesCombined,
  ScrollText,
  Settings,
  Info,
  ClipboardList,
  LogOut,
  Search,
  Bell,
  Menu,
  Plus,
  Play,
  RefreshCw,
  Download,
  CheckCircle2,
  AlertTriangle,
  LockKeyhole,
  HeartPulse,
  ChevronRight,
  Wifi,
  Fingerprint,
  X,
  Image as ImageIcon
} from 'lucide-react';
import { api, login, setToken, getToken } from './services/api';
import ImageDetection from './ImageDetection';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';

const nav = [
  ['Overview', '/overview', LayoutDashboard],
  ['Device Inventory', '/devices', Cpu],
  ['Device Authentication', '/authentication', Fingerprint],
  ['Behavioral AI Lab', '/behavior', Activity],
  ['Communication Security', '/communication', Radio],
  ['Network Traffic Analysis', '/network-traffic', Wifi],
  ['Image-Based Detection', '/image-detection', ImageIcon],
  ['Credential Monitoring', '/credentials', KeyRound],
  ['Firmware Integrity', '/firmware', FileCheck2],
  ['Trust & Risk Engine', '/risk', Gauge],
  ['Security Incidents', '/incidents', Siren],
  ['Network Topology', '/topology', Network],
  ['Guided Demo Lab', '/demo', FlaskConical],
  ['Simulation Table', '/simulation-table', ClipboardList],
  ['Research Evaluation', '/research', ChartNoAxesCombined],
  ['Model Comparison', '/model-comparison', ChartNoAxesCombined],
  ['Audit Logs', '/audit', ScrollText],
  ['Settings', '/settings', Settings],
  ['About Project', '/about', Info]
] as const;

type AnyObj = Record<string, any>;

function fmt(v: any) {
  if (!v) return '—';
  try {
    return new Date(v).toLocaleString();
  } catch {
    return String(v);
  }
}

function downloadJson(data: any, name: string) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
  a.download = name;
  a.click();
  URL.revokeObjectURL(a.href);
}

function Login({ onLogin }: { onLogin: (u: any) => void }) {
  const [u, setU] = useState('admin');
  const [p, setP] = useState('');
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(e: any) {
    e.preventDefault();
    setBusy(true);
    setErr('');
    try {
      onLogin(await login(u, p));
    } catch (ex: any) {
      setErr(ex.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-brand">
        <div className="brand-mark">
          <ShieldCheck size={28} />
        </div>
        <div>
          <b>MedSecure <span>Sentinel</span></b>
          <small>INTELLIGENT SECURITY FOR RESILIENT IOT ECOSYSTEMS</small>
        </div>
      </div>

      <div className="login-grid">
        <div className="login-copy">
          <div className="eyebrow"><span className="pulse-dot" /> CYBERSECURITY RESEARCH PLATFORM</div>
          <h1>Protecting connected care through <em>layered intelligence.</em></h1>
          <p>A hybrid multilayer cybersecurity framework for secure and resilient IoT ecosystems.</p>
          <div className="login-points">
            <span><CheckCircle2 /> Cryptographic device identity</span>
            <span><CheckCircle2 /> Behavioral anomaly detection</span>
            <span><CheckCircle2 /> Explainable risk assessment</span>
          </div>
        </div>

        <form className="login-card" onSubmit={submit}>
          <div className="card-icon"><LockKeyhole /></div>
          <h2>Welcome back</h2>
          <p>Sign in to your security operations workspace.</p>
          <label>
            Username
            <input value={u} onChange={e => setU(e.target.value)} autoComplete="username" required />
          </label>
          <label>
            Password
            <input type="password" value={p} onChange={e => setP(e.target.value)} autoComplete="current-password" required />
          </label>
          {err && <div className="error-box">{err}</div>}
          <button className="primary full" disabled={busy}>
            {busy ? 'Signing in…' : 'Sign in securely'} <ChevronRight size={16} />
          </button>
          <div className="login-foot">Development prototype · Simulated healthcare IoT data</div>
        </form>
      </div>

      <footer>© 2026 MedSecure Sentinel <span>Research prototype · Not for clinical use</span></footer>
    </div>
  );
}

function App() {
  const [user, setUser] = useState<AnyObj | null>(null);
  const [collapsed, setCollapsed] = useState(false);
  const [mobile, setMobile] = useState(false);
  const [online, setOnline] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    if (getToken()) {
      api('/auth/me')
        .then(setUser)
        .catch(() => {
          setToken('');
          setUser(null);
        });
    }
  }, []);

  useEffect(() => {
    fetch((import.meta.env.VITE_API_ROOT || 'http://localhost:8000') + '/health')
      .then(r => setOnline(r.ok))
      .catch(() => setOnline(false));
  }, [location.pathname]);

  if (!user) {
    return (
      <Login
        onLogin={u => {
          setUser(u);
          navigate('/overview');
        }}
      />
    );
  }

  const current = nav.find(n => n[1] === location.pathname) || nav[0];

  function logout() {
    setToken('');
    setUser(null);
    navigate('/');
  }

  return (
    <div className={`app-shell ${collapsed ? 'collapsed' : ''}`}>
      <aside className={`sidebar ${mobile ? 'mobile-open' : ''}`}>
        <div className="side-brand">
          <div className="brand-mark small"><ShieldCheck /></div>
          {!collapsed && (
            <div>
              <b>MedSecure <span>Sentinel</span></b>
              <small>SECURITY PLATFORM</small>
            </div>
          )}
          <button className="icon-btn mobile-close" onClick={() => setMobile(false)}><X /></button>
        </div>

        <div className="workspace-label">{!collapsed ? 'WORKSPACE' : ''}</div>

        <nav>
          {nav.map(([label, path, Icon]) => (
            <button
              key={path}
              className={`nav-link ${location.pathname === path ? 'active' : ''}`}
              title={label}
              onClick={() => {
                navigate(path);
                setMobile(false);
              }}
            >
              <Icon size={18} />
              {!collapsed && <span>{label}</span>}
              {location.pathname === path && !collapsed && <i />}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="prototype-box">
            <span className="status-dot" />
            {!collapsed && (
              <div>
                <b>Prototype environment</b>
                <small>All events are simulated</small>
              </div>
            )}
          </div>
          <button className="nav-link logout" onClick={logout}>
            <LogOut size={18} />
            {!collapsed && <span>Sign out</span>}
          </button>
          <button className="collapse-btn" onClick={() => setCollapsed(!collapsed)}>
            {collapsed ? '›' : '‹'} {!collapsed && 'Collapse sidebar'}
          </button>
        </div>
      </aside>

      {mobile && <div className="mobile-scrim" onClick={() => setMobile(false)} />}

      <main className="main-area">
        <header className="topbar">
          <div className="top-left">
            <button className="icon-btn mobile-menu" onClick={() => setMobile(true)}><Menu /></button>
            <div className="breadcrumbs">Workspace <ChevronRight size={13} /><b>{current[0]}</b></div>
          </div>
          <div className="top-actions">
            <div className={`api-status ${online ? '' : 'offline'}`}>
              <span className="status-dot" />
              {online ? 'API connected' : 'API offline'}
            </div>
            <div className="synthetic-tag"><Activity size={13} /> SYNTHETIC DATA</div>
            <button className="icon-btn" title="Notifications" onClick={() => navigate('/incidents')}>
              <Bell size={18} />
              <i className="notify-dot" />
            </button>
            <div className="user-chip">
              <div className="avatar">{user.username?.[0]?.toUpperCase()}</div>
              <div>
                <b>{user.username}</b>
                <small>{user.role}</small>
              </div>
            </div>
          </div>
        </header>

        <div className="page-wrap">
          <Routes>
            <Route path="/" element={<Navigate to="/overview" replace />} />
            <Route path="/overview" element={<Dashboard />} />
            <Route path="/devices" element={<Devices role={user.role} />} />
            <Route path="/authentication" element={<Authentication />} />
            <Route path="/behavior" element={<Behavior />} />
            <Route path="/communication" element={<Communication />} />
            <Route path="/network-traffic" element={<NetworkTrafficAnalysis />} />
            <Route path="/image-detection" element={<ImageDetection />} />
            <Route
              path="/credentials"
              element={
                <ScenarioPage
                  title="Credential Monitoring"
                  subtitle="Identify repeated failed authentication and replay-like patterns."
                  scenario="credential-misuse"
                  icon={<KeyRound />}
                />
              }
            />
            <Route path="/firmware" element={<Firmware />} />
            <Route path="/risk" element={<Risk />} />
            <Route path="/incidents" element={<Incidents />} />
            <Route path="/topology" element={<Topology />} />
            <Route path="/demo" element={<Demo />} />
            <Route path="/simulation-table" element={<SimulationTable />} />
            <Route path="/research" element={<Research />} />
            <Route path="/model-comparison" element={<ModelComparison />} />
            <Route path="/audit" element={<AuditPage />} />
            <Route path="/settings" element={<SettingsPage role={user.role} />} />
            <Route path="/about" element={<About />} />
            <Route path="*" element={<Navigate to="/overview" replace />} />
          </Routes>
        </div>

        <footer className="app-footer">
          <span>MEDSECURE SENTINEL <b>·</b> ACADEMIC RESEARCH PROTOTYPE</span>
          <span>v1.0.0 <b>·</b> Not validated for clinical deployment</span>
        </footer>
      </main>
    </div>
  );
}

function PageHeader({
  eyebrow,
  title,
  subtitle,
  action
}: {
  eyebrow: string;
  title: string;
  subtitle: string;
  action?: any;
}) {
  return (
    <div className="page-heading">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>
      {action && <div className="heading-action">{action}</div>}
    </div>
  );
}

function Loading() {
  return (
    <div className="loading">
      <RefreshCw className="spin" /> Loading API data…
    </div>
  );
}

function Empty({ text = 'No records yet. Initialize sample data or run a guided simulation.' }: { text?: string }) {
  return (
    <div className="empty-state">
      <div><Activity /></div>
      <b>Nothing to display yet</b>
      <p>{text}</p>
    </div>
  );
}

function useApi<T = any>(path: string, refresh: number = 0) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let live = true;
    setLoading(true);
    api<T>(path)
      .then(d => {
        if (live) {
          setData(d);
          setError('');
        }
      })
      .catch(e => {
        if (live) setError(e.message);
      })
      .finally(() => live && setLoading(false));
    return () => {
      live = false;
    };
  }, [path, refresh]);

  return { data, error, loading };
}

function Metric({
  label,
  value,
  icon: Icon,
  tone = 'cyan',
  hint
}: {
  label: string;
  value: any;
  icon: any;
  tone?: string;
  hint?: string;
}) {
  return (
    <div className="metric-card">
      <div className={`metric-icon ${tone}`}><Icon size={19} /></div>
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value ?? '—'}</div>
      <div className="metric-hint">{hint || 'From persisted API records'}</div>
    </div>
  );
}

function Section({ title, extra, children }: { title: string; extra?: any; children: any }) {
  return (
    <section className="panel">
      <div className="panel-head">
        <h3>{title}</h3>
        {extra}
      </div>
      {children}
    </section>
  );
}

function Severity({ value }: { value: string }) {
  return <span className={`severity ${(value || 'low').toLowerCase()}`}>{value || 'Unknown'}</span>;
}

function Table({
  columns,
  rows,
  empty
}: {
  columns: { key: string; label: string; render?: (v: any, r: any) => any }[];
  rows: any[];
  empty?: string;
}) {
  if (!rows?.length) return <Empty text={empty} />;
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            {columns.map(c => (
              <th key={c.key}>{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={r.id || r.device_id || i}>
              {columns.map(c => (
                <td key={c.key}>
                  {c.render
                    ? c.render(r[c.key], r)
                    : r[c.key] === null || r[c.key] === undefined
                      ? '—'
                      : typeof r[c.key] === 'object'
                        ? JSON.stringify(r[c.key])
                        : String(r[c.key])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ErrorPanel({ error }: { error: string }) {
  return (
    <div className="error-panel">
      <AlertTriangle />
      <div>
        <b>Could not load API data</b>
        <p>
          {error}. Ensure the FastAPI backend is running at <code>http://localhost:8000</code> and sign in again.
        </p>
      </div>
    </div>
  );
}

function Dashboard() {
  const [refresh, setRefresh] = useState(0);
  const navigate = useNavigate();
  const { data, error, loading } = useApi<AnyObj>('/dashboard', refresh);

  if (loading) return <Loading />;
  if (error) return <ErrorPanel error={error} />;
  const d = data!;

  return (
    <>
      <PageHeader
        eyebrow="SECURITY OPERATIONS / OVERVIEW"
        title="Security overview"
        subtitle="A unified view of simulated healthcare IoT security posture and recent detections."
        action={
          <button className="secondary" onClick={() => setRefresh(refresh + 1)}>
            <RefreshCw size={15} /> Refresh data
          </button>
        }
      />

      <div className="notice">
        <Activity size={16} />
        <span>
          <b>Simulation environment</b> All devices, telemetry, incidents, and security events shown here are synthetic research data.
        </span>
      </div>

      <div className="metrics-grid">
        <Metric label="Registered devices" value={d.total_devices} icon={Cpu} />
        <Metric label="Low risk" value={d.low_risk} icon={ShieldCheck} tone="green" />
        <Metric label="Needs attention" value={d.attention} icon={AlertTriangle} tone="amber" />
        <Metric label="High / critical" value={d.high_critical} icon={Siren} tone="red" />
        <Metric label="Auth failures" value={d.authentication_failures} icon={Fingerprint} tone="amber" />
        <Metric label="Open incidents" value={d.open_incidents} icon={Bell} tone="red" />
      </div>

      <div className="two-col">
        <Section title="Device risk distribution">
          <div className="risk-bars">
            {Object.entries(d.risk_distribution || {}).map(([k, v]: any) => (
              <div className="risk-row" key={k}>
                <div>
                  <Severity value={k} />
                  <b>{v}</b>
                </div>
                <div className="bar-track">
                  <div
                    className={`bar-fill ${k.toLowerCase()}`}
                    style={{ width: `${d.total_devices ? Math.max(0, (v / d.total_devices) * 100) : 0}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
          <div className="chart-foot">Risk categories are derived from the latest persisted prototype risk assessment.</div>
        </Section>

        <Section title="Security event categories">
          <div className="category-list">
            {Object.entries(d.events_by_category || {})
              .sort((a: any, b: any) => b[1] - a[1])
              .slice(0, 7)
              .map(([k, v]: any) => (
                <div className="category-row" key={k}>
                  <span className="category-dot" />
                  <span>{k}</span>
                  <b>{v}</b>
                </div>
              ))}
          </div>
        </Section>
      </div>

      <Section
        title="Recent security events"
        extra={
          <button className="text-btn" onClick={() => navigate('/audit')}>
            View audit trail <ChevronRight size={14} />
          </button>
        }
      >
        <Table
          rows={d.recent_events}
          columns={[
            { key: 'created_at', label: 'Time', render: v => fmt(v) },
            { key: 'title', label: 'Event' },
            { key: 'device_id', label: 'Device' },
            { key: 'category', label: 'Layer' },
            { key: 'severity', label: 'Severity', render: v => <Severity value={v} /> }
          ]}
        />
      </Section>

      <Section title="Highest-risk devices">
        <Table
          rows={[...(d.devices || [])].sort((a: any, b: any) => b.risk_score - a.risk_score).slice(0, 5)}
          columns={[
            { key: 'name', label: 'Device' },
            { key: 'device_id', label: 'Device ID' },
            { key: 'risk_score', label: 'Risk score', render: v => <b>{v}</b> },
            { key: 'risk_category', label: 'Risk', render: v => <Severity value={v} /> },
            { key: 'trust_score', label: 'Trust', render: v => `${v}%` }
          ]}
        />
      </Section>
    </>
  );
}

function Devices({ role }: { role: string }) {
  const [refresh, setRefresh] = useState(0);
  const [search, setSearch] = useState('');
  const [risk, setRisk] = useState('');
  const [show, setShow] = useState(false);
  const [msg, setMsg] = useState('');
  const { data, error, loading } = useApi<AnyObj>(
    `/devices?search=${encodeURIComponent(search)}&risk=${encodeURIComponent(risk)}`,
    refresh
  );
  const [form, setForm] = useState({
    device_id: 'SIM-006',
    name: 'New simulated sensor',
    device_type: 'Wearable sensor',
    manufacturer: 'Synthetic Vendor',
    firmware_version: '1.0.0',
    ip_address: '192.0.2.16',
    location: 'Simulated Ward B'
  });

  async function add(e: any) {
    e.preventDefault();
    try {
      await api('/devices', { method: 'POST', body: JSON.stringify(form) });
      setShow(false);
      setMsg('Device registered with a simulated RSA key pair.');
      setRefresh(refresh + 1);
    } catch (ex: any) {
      setMsg(ex.message);
    }
  }

  function exportCsv() {
    const rows = data?.items || [];
    const keys = [
      'device_id',
      'name',
      'device_type',
      'firmware_version',
      'ip_address',
      'location',
      'risk_score',
      'trust_score',
      'risk_category'
    ];
    const csv = [
      keys.join(','),
      ...rows.map((r: any) => keys.map(k => JSON.stringify(r[k] ?? '')).join(','))
    ].join('\n');
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
    a.download = 'medsecure-devices.csv';
    a.click();
    URL.revokeObjectURL(a.href);
  }

  return (
    <>
      <PageHeader
        eyebrow="ASSET MANAGEMENT"
        title="Device inventory"
        subtitle="Register, search, and inspect synthetic healthcare IoT devices."
        action={
          <>
            {role === 'administrator' && (
              <button className="primary" onClick={() => setShow(!show)}>
                <Plus size={16} /> Register device
              </button>
            )}
            <button className="secondary" onClick={exportCsv}>
              <Download size={15} /> Export CSV
            </button>
          </>
        }
      />

      {msg && <div className="notice">{msg}</div>}

      {show && (
        <Section title="Register simulated device">
          <form className="device-form" onSubmit={add}>
            {Object.entries(form).map(([k, v]) => (
              <label key={k}>
                {k.replaceAll('_', ' ')}
                <input value={v} onChange={e => setForm({ ...form, [k]: e.target.value })} required />
              </label>
            ))}
            <button className="primary">Create device</button>
          </form>
        </Section>
      )}

      <div className="filter-row">
        <div className="search-box">
          <Search size={16} />
          <input placeholder="Search devices, IDs, or types…" value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <select value={risk} onChange={e => setRisk(e.target.value)}>
          <option value="">All risk levels</option>
          {['Low', 'Medium', 'High', 'Critical'].map(x => (
            <option key={x}>{x}</option>
          ))}
        </select>
        <button className="secondary" onClick={() => setRefresh(refresh + 1)}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorPanel error={error} />
      ) : (
        <Section title={`${data?.total || 0} registered devices`}>
          <Table
            rows={data?.items || []}
            columns={[
              {
                key: 'name',
                label: 'Device',
                render: (v, r) => (
                  <div className="device-cell">
                    <div className="device-symbol"><HeartPulse size={16} /></div>
                    <div>
                      <b>{v}</b>
                      <small>{r.device_id}</small>
                    </div>
                  </div>
                )
              },
              { key: 'device_type', label: 'Type' },
              { key: 'firmware_version', label: 'Firmware' },
              { key: 'risk_category', label: 'Risk status', render: v => <Severity value={v} /> },
              { key: 'risk_score', label: 'Risk score', render: v => <b>{v}</b> },
              { key: 'trust_score', label: 'Trust score', render: v => `${v}%` },
              { key: 'location', label: 'Location' }
            ]}
          />
        </Section>
      )}

      <div className="footnote">
        Private key material is not returned by device APIs. Local development signing keys are stored under backend/device_keys; protect this directory.
      </div>
    </>
  );
}

function ScenarioPage({
  title,
  subtitle,
  scenario,
  icon
}: {
  title: string;
  subtitle: string;
  scenario: string;
  icon: any;
}) {
  const [result, setResult] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  async function run() {
    setBusy(true);
    setErr('');
    try {
      setResult(await api(`/simulations/${scenario}`, { method: 'POST', body: JSON.stringify({}) }));
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeader eyebrow="DETECTION LAYER" title={title} subtitle={subtitle} />

      <div className="feature-banner">
        <div className="feature-icon">{icon}</div>
        <div>
          <h3>Controlled scenario runner</h3>
          <p>Run a reproducible simulation through the backend, persist the event, and inspect evidence and risk impact.</p>
        </div>
        <button className="primary" onClick={run} disabled={busy}>
          <Play size={15} />
          {busy ? 'Running…' : 'Run simulation'}
        </button>
      </div>

      {err && <div className="error-box">{err}</div>}
      {result && <ResultCard result={result} />}
    </>
  );
}

function ResultCard({ result }: { result: any }) {
  return (
    <div className="result-stack">
      <div className="result-header">
        <CheckCircle2 />
        <div>
          <b>Simulation completed</b>
          <p>Scenario: {result.scenario} · Synthetic data persisted</p>
        </div>
      </div>

      <div className="metrics-grid compact">
        <Metric label="Risk before" value={result.before?.risk_score ?? '—'} icon={Gauge} />
        <Metric label="Risk after" value={result.after?.risk_score ?? '—'} icon={AlertTriangle} tone="red" />
        <Metric label="Trust after" value={result.after?.trust_score ?? '—'} icon={ShieldCheck} tone="green" />
        <Metric label="Risk category" value={result.after?.risk_category ?? '—'} icon={Activity} />
      </div>

      <Section title="Scenario evidence">
        <pre className="json-view">{JSON.stringify(result.results, null, 2)}</pre>
      </Section>

      <Section title="Risk assessment explanation">
        <pre className="json-view">{JSON.stringify(result.risk_assessment, null, 2)}</pre>
      </Section>
    </div>
  );
}

function Demo() {
  const scenarios = [
    ['normal', 'A · Normal device operation', 'Valid simulated authentication, baseline telemetry, and trusted firmware.'],
    ['invalid-signature', 'B · Invalid device signature', 'Reject an invalid signature and create an investigation event.'],
    ['abnormal-behavior', 'C · Abnormal device behavior', 'Run Isolation Forest against unusual synthetic telemetry.'],
    ['suspicious-communication', 'D · Suspicious communication', 'Generate latency, jitter, packet-loss, and reconnection indicators.'],
    ['credential-misuse', 'E · Credential misuse', 'Generate repeated authentication failures above the configured threshold.'],
    ['tampered-firmware', 'F · Tampered firmware', 'Simulate a firmware digest mismatch.'],
    ['firmware-downgrade', 'G · Firmware downgrade', 'Check a version below the configured minimum policy.'],
    ['combined', 'H · Combined multilayer incident', 'Generate evidence across all five security layers and consolidate an incident.']
  ];

  const labels: Record<string, string> = {
    normal: 'Normal',
    'invalid-signature': 'Invalid Signature',
    'abnormal-behavior': 'Abnormal Behavior',
    'suspicious-communication': 'Suspicious Communication',
    'credential-misuse': 'Credential Misuse',
    'tampered-firmware': 'Tampered Firmware',
    'firmware-downgrade': 'Firmware Downgrade',
    combined: 'Combined Incident'
  };

  const [active, setActive] = useState('combined');
  const [result, setResult] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function run() {
    setBusy(true);
    setError('');

    try {
      const response = await api<any>(`/simulations/${active}`, {
        method: 'POST',
        body: JSON.stringify({ seed: 42 })
      });

      setResult(response);

      const beforeRisk = Number(response.before?.risk_score ?? 0);
      const afterRisk = Number(response.after?.risk_score ?? 0);
      const scenarioName = scenarios.find(s => s[0] === active)?.[1] || active;

      const row = {
        id: `${Date.now()}-${active}`,
        scenario: active,
        name: scenarioName,
        label: labels[active] || active,
        device_id: response.device_id || '—',
        beforeRisk,
        afterRisk,
        riskChange: afterRisk - beforeRisk,
        category: response.after?.risk_category || 'Unknown'
      };

      setHistory(previous => [row, ...previous]);
    } catch (e: any) {
      setError(e.message || 'Simulation failed.');
    } finally {
      setBusy(false);
    }
  }

  const chartData = [...history].reverse();

  return (
    <>
      <PageHeader
        eyebrow="LECTURER DEMONSTRATION"
        title="Guided demo lab"
        subtitle="Execute eight reproducible security scenarios and compare their recorded risk scores."
      />

      <div className="demo-layout">
        <div className="scenario-list">
          {scenarios.map(([id, name, desc], index) => (
            <button
              key={id}
              className={`scenario-choice ${active === id ? 'selected' : ''}`}
              onClick={() => {
                setActive(id);
                setResult(null);
                setError('');
              }}
            >
              <div className="scenario-number">{String(index + 1).padStart(2, '0')}</div>
              <div>
                <b>{name}</b>
                <small>{desc}</small>
              </div>
              <ChevronRight size={16} />
            </button>
          ))}
        </div>

        <div className="scenario-detail">
          <div className="eyebrow">SELECTED SCENARIO</div>
          <h2>{scenarios.find(s => s[0] === active)?.[1]}</h2>
          <p>{scenarios.find(s => s[0] === active)?.[2]}</p>

          <div className="detail-tags">
            <span>Simulated</span>
            <span>API executed</span>
            <span>Persisted evidence</span>
          </div>

          <button className="primary full" onClick={run} disabled={busy}>
            <Play size={16} />
            {busy ? 'Executing scenario…' : 'Execute scenario'}
          </button>

          {error && <div className="error-box">{error}</div>}

          {result && (
            <div className="mini-result">
              <b>
                <CheckCircle2 size={16} /> Simulation completed
              </b>
              <p>
                Risk score: {result.before?.risk_score ?? '—'}
                {' → '}
                {result.after?.risk_score ?? '—'}
              </p>
              <p>
                Trust score: {result.after?.trust_score ?? '—'}
                {' · '}
                {result.after?.risk_category ?? 'Unknown'} risk
              </p>
              <button
                className="secondary full"
                onClick={() =>
                  document.getElementById('scenario-result')?.scrollIntoView({ behavior: 'smooth' })
                }
              >
                View full evidence
              </button>
            </div>
          )}
        </div>
      </div>

      <Section
        title="Simulation history"
        extra={
          <button className="secondary" onClick={() => setHistory([])} disabled={history.length === 0}>
            Clear history
          </button>
        }
      >
        <p className="muted">
          Results from scenarios executed during this browser session. History clears when you refresh the page.
        </p>

        <div className="metrics-grid compact">
          <Metric label="Simulations completed" value={history.length} icon={FlaskConical} />
          <Metric label="Latest risk score" value={history.length ? history[0].afterRisk : '—'} icon={Gauge} />
          <Metric
            label="Latest risk change"
            value={history.length ? `${history[0].riskChange > 0 ? '+' : ''}${history[0].riskChange}` : '—'}
            icon={Activity}
          />
          <Metric label="Latest risk category" value={history.length ? history[0].category : '—'} icon={ShieldCheck} />
        </div>

        {history.length > 0 ? (
          <div style={{ width: '100%', height: 320, marginTop: 24 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                margin={{ top: 20, right: 25, left: 10, bottom: 10 }}
                barGap={8}
                barCategoryGap="25%"
              >
                <CartesianGrid stroke="#334155" strokeDasharray="4 4" vertical={false} />

                <XAxis
                  dataKey="label"
                  tick={{ fill: '#CBD5E1', fontSize: 12 }}
                  axisLine={{ stroke: '#475569' }}
                  tickLine={{ stroke: '#475569' }}
                />

                <YAxis
                  domain={[0, 100]}
                  ticks={[0, 20, 40, 60, 80, 100]}
                  tick={{ fill: '#CBD5E1', fontSize: 12 }}
                  axisLine={{ stroke: '#475569' }}
                  tickLine={false}
                  label={{
                    value: 'Risk score',
                    angle: -90,
                    position: 'insideLeft',
                    fill: '#CBD5E1',
                    fontSize: 13
                  }}
                />

                <Tooltip
                  cursor={{ fill: 'rgba(148, 163, 184, 0.10)' }}
                  contentStyle={{
                    backgroundColor: '#0F172A',
                    border: '1px solid #334155',
                    borderRadius: '10px',
                    color: '#F8FAFC',
                    padding: '12px'
                  }}
                  labelStyle={{
                    color: '#67E8F9',
                    fontWeight: 600,
                    marginBottom: '6px'
                  }}
                  itemStyle={{ color: '#E2E8F0' }}
                />

                <Legend
                  wrapperStyle={{
                    color: '#CBD5E1',
                    paddingTop: '12px',
                    fontSize: '13px'
                  }}
                />

                <Bar dataKey="beforeRisk" name="Risk before" fill="#60A5FA" radius={[5, 5, 0, 0]} maxBarSize={45} />
                <Bar dataKey="afterRisk" name="Risk after" fill="#22D3EE" radius={[5, 5, 0, 0]} maxBarSize={45} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <Empty text="Run a scenario to generate your first risk comparison graph and table." />
        )}
      </Section>

      <Section title="Scenario comparison table">
        <Table
          rows={history}
          empty="No simulation results yet. Select a scenario and execute it first."
          columns={[
            { key: 'name', label: 'Scenario' },
            { key: 'device_id', label: 'Device ID' },
            { key: 'beforeRisk', label: 'Risk before' },
            { key: 'afterRisk', label: 'Risk after' },
            {
              key: 'riskChange',
              label: 'Risk change',
              render: (value: number) => (
                <b>
                  {value > 0 ? '+' : ''}
                  {value}
                </b>
              )
            },
            {
              key: 'category',
              label: 'Final risk category',
              render: (value: string) => <Severity value={value} />
            }
          ]}
        />
      </Section>

      {result && (
        <div id="scenario-result">
          <ResultCard result={result} />
        </div>
      )}
    </>
  );
}

function Authentication() {
  const { data, error, loading } = useApi<AnyObj>('/devices');
  const [device, setDevice] = useState('');
  const [challenge, setChallenge] = useState<any>(null);
  const [signature, setSignature] = useState('');
  const [result, setResult] = useState<any>(null);
  const [err, setErr] = useState('');

  useEffect(() => {
    if (data?.items?.length && !device) setDevice(data.items[0].device_id);
  }, [data]);

  async function create() {
    try {
      setErr('');
      setChallenge(await api(`/authentication/${device}/challenge`, { method: 'POST' }));
      setResult(null);
    } catch (e: any) {
      setErr(e.message);
    }
  }

  async function sign() {
    try {
      const r = await api<any>(
        `/authentication/${device}/simulate-sign?nonce=${encodeURIComponent(challenge.nonce)}`,
        { method: 'POST' }
      );
      setSignature(r.signature);
    } catch (e: any) {
      setErr(e.message);
    }
  }

  async function verify() {
    try {
      setResult(
        await api(`/authentication/${device}/verify?nonce=${encodeURIComponent(challenge.nonce)}`, {
          method: 'POST',
          body: JSON.stringify({ signature })
        })
      );
    } catch (e: any) {
      setErr(e.message);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="CRYPTOGRAPHIC IDENTITY"
        title="Device authentication"
        subtitle="RSA-PSS with SHA-256 challenge-response verification and one-time challenge protection."
      />

      <div className="two-col">
        <Section title="Challenge-response workflow">
          <p className="muted">
            Choose a simulated device, generate a short-lived challenge, sign it in local demo mode, then verify the signature.
          </p>

          <label className="field-label">
            Device
            <select
              value={device}
              onChange={e => {
                setDevice(e.target.value);
                setChallenge(null);
                setSignature('');
              }}
            >
              {(data?.items || []).map((d: any) => (
                <option key={d.device_id} value={d.device_id}>
                  {d.name} ({d.device_id})
                </option>
              ))}
            </select>
          </label>

          <div className="button-row">
            <button className="primary" onClick={create} disabled={!device}>
              <Plus size={15} /> Generate challenge
            </button>
            {challenge && (
              <button className="secondary" onClick={sign}>
                <Fingerprint size={15} /> Simulate sign
              </button>
            )}
          </div>

          {challenge && (
            <>
              <label className="field-label">
                Challenge payload
                <textarea readOnly rows={5} value={challenge.payload} />
              </label>
              <small className="muted">Expires: {fmt(challenge.expires_at)}</small>
              <label className="field-label">
                Signature
                <textarea
                  value={signature}
                  onChange={e => setSignature(e.target.value)}
                  rows={3}
                  placeholder="Simulated signature appears here; you may modify it to test rejection."
                />
              </label>
              <button className="primary" onClick={verify} disabled={!signature}>
                Verify signature
              </button>
            </>
          )}

          {err && <div className="error-box">{err}</div>}

          {result && (
            <div className={result.verified ? 'success-box' : 'error-box'}>
              <b>{result.status}</b>
              <p>{result.algorithm} · Fingerprint {result.fingerprint}</p>
            </div>
          )}
        </Section>

        <Section title="Security properties">
          <div className="security-list">
            <div>
              <CheckCircle2 />
              <span>
                <b>Cryptographically random challenge</b>
                <small>Nonce is generated using secure random bytes.</small>
              </span>
            </div>
            <div>
              <CheckCircle2 />
              <span>
                <b>Two-minute expiry</b>
                <small>Expired challenges are rejected by the backend.</small>
              </span>
            </div>
            <div>
              <CheckCircle2 />
              <span>
                <b>Replay prevention</b>
                <small>Challenge is marked consumed after verification.</small>
              </span>
            </div>
            <div>
              <AlertTriangle />
              <span>
                <b>Simulation limitation</b>
                <small>Demo signing uses a local private key. It does not prove physical device integrity.</small>
              </span>
            </div>
          </div>
        </Section>
      </div>

      {loading && <Loading />}
      {error && <ErrorPanel error={error} />}
    </>
  );
}

function Behavior() {
  const [form, setForm] = useState({
    packet_rate: 130,
    response_ms: 190,
    cpu_pct: 92,
    memory_pct: 93,
    failed_requests: 9,
    connection_frequency: 14,
    bytes_sent: 95000,
    session_seconds: 40,
    reconnections: 6,
    error_frequency: 8
  });
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  const { data: evalData } = useApi<any>('/research/evaluation');

  async function run() {
    try {
      setError('');
      setResult(await api('/analysis/behavior', { method: 'POST', body: JSON.stringify({ sample: form }) }));
    } catch (e: any) {
      setError(e.message);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="MACHINE LEARNING"
        title="Behavioral AI lab"
        subtitle="Isolation Forest identifies unusual numeric patterns in synthetic device telemetry; the score is not an attack probability."
      />

      <div className="two-col">
        <Section title="Single-sample inference">
          <div className="feature-form">
            {Object.entries(form).map(([k, v]) => (
              <label key={k}>
                {k.replaceAll('_', ' ')}
                <input type="number" value={v} onChange={e => setForm({ ...form, [k]: Number(e.target.value) })} />
              </label>
            ))}
          </div>

          <button className="primary" onClick={run}>
            <Activity size={16} /> Analyze telemetry
          </button>

          {error && <div className="error-box">{error}</div>}

          {result && (
            <div className="ml-result">
              <div className="eyebrow">INFERENCE RESULT</div>
              <h2><Severity value={result.classification} /></h2>
              <p>Decision score: <b>{Number(result.decision_score).toFixed(4)}</b></p>
              <p className="muted">This score is not a calibrated probability.</p>
              <Table
                rows={result.unusual_features || []}
                columns={[
                  { key: 'feature', label: 'Feature' },
                  { key: 'value', label: 'Observed' },
                  { key: 'baseline_mean', label: 'Baseline mean' },
                  { key: 'deviation_sigma', label: 'Deviation (σ)' }
                ]}
                empty="No features exceeded the transparent 2.5σ explanation threshold."
              />
            </div>
          )}
        </Section>

        <Section title="Held-out synthetic evaluation">
          <p className="muted">Reproducible generated benchmark. Not representative of real hospital traffic.</p>

          {evalData && (
            <div className="metrics-grid compact">
              <Metric label="Precision" value={(evalData.precision * 100).toFixed(1) + '%'} icon={Gauge} />
              <Metric label="Recall" value={(evalData.recall * 100).toFixed(1) + '%'} icon={Activity} />
              <Metric label="F1 score" value={evalData.f1.toFixed(3)} icon={ChartNoAxesCombined} />
              <Metric label="Test samples" value={evalData.test_samples} icon={Cpu} />
            </div>
          )}

          {evalData && (
            <Table
              rows={[
                { metric: 'True positive', value: evalData.true_positive },
                { metric: 'True negative', value: evalData.true_negative },
                { metric: 'False positive', value: evalData.false_positive },
                { metric: 'False negative', value: evalData.false_negative },
                { metric: 'False-positive rate', value: evalData.false_positive_rate.toFixed(3) },
                {
                  metric: 'False-negative rate',
                  value: (
                    evalData.false_negative / Math.max(1, evalData.false_negative + evalData.true_positive)
                  ).toFixed(3)
                }
              ]}
              columns={[
                { key: 'metric', label: 'Metric' },
                { key: 'value', label: 'Measured value' }
              ]}
            />
          )}
        </Section>
      </div>
    </>
  );
}

function Communication() {
  return (
    <ScenarioPage
      title="Communication security"
      subtitle="Rule-based analysis of simulated latency, jitter, packet loss, and reconnection patterns."
      scenario="suspicious-communication"
      icon={<Radio />}
    />
  );
}

function Firmware() {
  return (
    <>
      <PageHeader
        eyebrow="INTEGRITY & VERSION POLICY"
        title="Firmware integrity"
        subtitle="SHA-256 digest comparison and downgrade-policy simulation. Uploaded firmware is never executed."
      />

      <div className="notice">
        <LockKeyhole size={16} /> Hashes detect changes only when compared with a trusted expected digest. A hash alone does not establish authenticity.
      </div>

      <ScenarioPage
        title="Tampered firmware simulation"
        subtitle="Generate a digest mismatch event against synthetic trusted metadata."
        scenario="tampered-firmware"
        icon={<FileCheck2 />}
      />

      <ScenarioPage
        title="Rollback protection"
        subtitle="Simulate an attempted version below the configured minimum policy."
        scenario="firmware-downgrade"
        icon={<ShieldCheck />}
      />
    </>
  );
}

function Risk() {
  const { data, error, loading } = useApi<any>('/devices');
  const [selected, setSelected] = useState('');
  const [result, setResult] = useState<any>(null);
  const [err, setErr] = useState('');

  useEffect(() => {
    if (data?.items?.length && !selected) setSelected(data.items[0].device_id);
  }, [data]);

  async function recalc() {
    try {
      setErr('');
      setResult(await api(`/risk/${selected}/recalculate`, { method: 'POST' }));
    } catch (e: any) {
      setErr(e.message);
    }
  }

  const bands = [
    ['Low', '0–24', 'Routine monitoring'],
    ['Medium', '25–49', 'Review evidence'],
    ['High', '50–74', 'Investigate promptly'],
    ['Critical', '75–100', 'Prioritize incident response']
  ];

  return (
    <>
      <PageHeader
        eyebrow="EXPLAINABLE TRUST"
        title="Trust & risk engine"
        subtitle="Weighted multilayer evidence aggregation with explicit coverage and unevaluated layers."
      />

      <div className="notice">
        <Gauge size={16} /> Prototype weights: authentication 25%, behavioral AI 20%, communication 20%, credential misuse 15%, firmware integrity 20%. These are assumptions, not validated constants.
      </div>

      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorPanel error={error} />
      ) : (
        <Section title="Device risk assessment">
          <div className="risk-controls">
            <label>
              Device
              <select value={selected} onChange={e => setSelected(e.target.value)}>
                {(data?.items || []).map((d: any) => (
                  <option key={d.device_id} value={d.device_id}>
                    {d.name} ({d.device_id})
                  </option>
                ))}
              </select>
            </label>
            <button className="primary" onClick={recalc} disabled={!selected}>
              <RefreshCw size={15} /> Recalculate
            </button>
          </div>

          {err && <div className="error-box">{err}</div>}

          <Table
            rows={data?.items || []}
            columns={[
              { key: 'name', label: 'Device' },
              { key: 'risk_score', label: 'Risk score' },
              { key: 'trust_score', label: 'Trust score' },
              { key: 'risk_category', label: 'Category', render: v => <Severity value={v} /> }
            ]}
          />
        </Section>
      )}

      {result && (
        <ResultCard
          result={{ scenario: 'risk-recalculation', before: {}, after: result, results: [], risk_assessment: result }}
        />
      )}

      <Section title="Risk bands">
        <div className="risk-band-grid">
          {bands.map(([a, b, c]) => (
            <div className="risk-band" key={a}>
              <Severity value={a} />
              <b>{b}</b>
              <small>{c}</small>
            </div>
          ))}
        </div>
      </Section>
    </>
  );
}

function Incidents() {
  const [refresh, setRefresh] = useState(0);
  const [filter, setFilter] = useState('');
  const { data, error, loading } = useApi<any>(`/incidents${filter ? '?status=' + filter : ''}`, refresh);
  const statuses = ['Open', 'Acknowledged', 'Investigating', 'Resolved'];

  async function update(id: number, status: string) {
    try {
      await api(`/incidents/${id}`, { method: 'PATCH', body: JSON.stringify({ status }) });
      setRefresh(refresh + 1);
    } catch (e: any) {
      alert(e.message);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="INCIDENT RESPONSE"
        title="Security incidents"
        subtitle="Investigate detection events and record incident lifecycle transitions."
        action={
          <button className="secondary" onClick={() => setRefresh(refresh + 1)}>
            <RefreshCw size={15} /> Refresh
          </button>
        }
      />

      <div className="filter-row">
        <span className="muted">Filter by status</span>
        <select value={filter} onChange={e => setFilter(e.target.value)}>
          <option value="">All statuses</option>
          {statuses.map(x => (
            <option key={x}>{x}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorPanel error={error} />
      ) : (
        <Section title={`${data?.items?.length || 0} incidents`}>
          <Table
            rows={data?.items || []}
            columns={[
              { key: 'created_at', label: 'Created', render: v => fmt(v) },
              { key: 'title', label: 'Incident' },
              { key: 'device_id', label: 'Device' },
              { key: 'category', label: 'Source' },
              { key: 'severity', label: 'Severity', render: v => <Severity value={v} /> },
              { key: 'status', label: 'Status', render: v => <span className="status-pill">{v}</span> },
              {
                key: 'id',
                label: 'Actions',
                render: (v, r) => (
                  <select aria-label="Update incident status" value={r.status} onChange={e => update(v, e.target.value)}>
                    {statuses.map(s => (
                      <option key={s}>{s}</option>
                    ))}
                  </select>
                )
              }
            ]}
          />
        </Section>
      )}
    </>
  );
}

function Topology() {
  const { data, error, loading } = useApi<any>('/topology');

  return (
    <>
      <PageHeader
        eyebrow="SIMULATED CONNECTIVITY"
        title="Network topology"
        subtitle="Backend-derived device graph for the synthetic environment. Connections are illustrative, not live network observations."
      />

      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorPanel error={error} />
      ) : (
        <>
          <div className="topology-canvas">
            <div className="topology-note">
              <Network size={17} /> Synthetic topology · {data?.nodes?.length || 0} nodes · {data?.edges?.length || 0} links
            </div>

            <div className="topology-nodes">
              {(data?.nodes || []).map((n: any) => (
                <div className={`topology-node ${n.device.risk_category.toLowerCase()}`} key={n.id}>
                  <div className="topo-icon">{n.type === 'gateway' ? <Wifi /> : <HeartPulse />}</div>
                  <b>{n.label}</b>
                  <small>{n.id}</small>
                  <Severity value={n.device.risk_category} />
                  <span>Trust {n.device.trust_score}%</span>
                </div>
              ))}
            </div>

            <div className="topology-links">
              {(data?.edges || []).map((e: any) => (
                <span key={e.id} className={e.suspicious ? 'link-danger' : ''}>
                  {e.source} → {e.target} {e.suspicious ? '· suspicious' : ''}
                </span>
              ))}
            </div>
          </div>

          <Section title="Device connection records">
            <Table
              rows={data?.edges || []}
              columns={[
                { key: 'source', label: 'Source' },
                { key: 'target', label: 'Destination' },
                {
                  key: 'suspicious',
                  label: 'Flag',
                  render: v => (v ? <Severity value="High" /> : <Severity value="Low" />)
                }
              ]}
            />
          </Section>
        </>
      )}
    </>
  );
}

function NetworkTrafficAnalysis() {
  const categories = [
    { category: 'Normal', records: 14272 },
    { category: 'Spoofing', records: 1124 },
    { category: 'Data Alteration', records: 922 }
  ];
  const total = categories.reduce((sum, item) => sum + item.records, 0);
  const trafficFeatures = [
    { feature: 'TotPkts', meaning: 'Total packets recorded', average: '7.02' },
    { feature: 'TotBytes', meaning: 'Total bytes recorded', average: '683.73' },
    { feature: 'Rate', meaning: 'Traffic rate feature in the dataset', average: '428.72' },
    { feature: 'SrcLoad', meaning: 'Source-side load feature', average: '211,840.63' },
    { feature: 'DstLoad', meaning: 'Destination-side load feature', average: '71,024.35' },
    { feature: 'Loss', meaning: 'Packet-loss feature', average: '0.00' },
    { feature: 'SrcJitter', meaning: 'Source-side jitter feature', average: '32.03' },
    { feature: 'DstJitter', meaning: 'Destination-side jitter feature', average: '8.55' }
  ];
  const attackTotal = categories[1].records + categories[2].records;

  return (
    <>
      <PageHeader
        eyebrow="DATASET-BASED ANALYSIS"
        title="Network Traffic Analysis"
        subtitle="Explore network-related fields and the labelled traffic categories in the DMP IoMT dataset."
        action={
          <button className="secondary" onClick={() => window.print()}>
            <Download size={15} /> Print / save
          </button>
        }
      />

      <div className="notice">
        <Wifi size={16} />
        <span>
          <b>Offline dataset analysis</b> This page summarizes the existing my_data.csv dataset. It does not capture live network packets or perform live intrusion detection.
        </span>
      </div>

      <div className="metrics-grid">
        <Metric label="Dataset records" value={total.toLocaleString()} icon={Activity} hint="Rows in my_data.csv" />
        <Metric label="Dataset columns" value="45" icon={ChartNoAxesCombined} hint="Fields available for analysis" />
        <Metric
          label="Normal records"
          value={categories[0].records.toLocaleString()}
          icon={ShieldCheck}
          tone="green"
          hint={`${((categories[0].records / total) * 100).toFixed(2)}% of records`}
        />
        <Metric
          label="Labelled attack records"
          value={attackTotal.toLocaleString()}
          icon={AlertTriangle}
          tone="amber"
          hint={`${((attackTotal / total) * 100).toFixed(2)}% of records`}
        />
      </div>

      <Section title="Traffic / attack category distribution">
        <div style={{ width: '100%', height: 300 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={categories} margin={{ top: 12, right: 20, left: 8, bottom: 12 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="category" />
              <YAxis allowDecimals={false} />
              <Tooltip formatter={(value: any) => [Number(value).toLocaleString(), 'Records']} />
              <Legend />
              <Bar dataKey="records" name="Records" fill="#20b8b2" radius={[5, 5, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <Table
          rows={categories.map(item => ({
            category: item.category,
            records: item.records.toLocaleString(),
            share: `${((item.records / total) * 100).toFixed(2)}%`
          }))}
          columns={[
            { key: 'category', label: 'Category' },
            { key: 'records', label: 'Records' },
            { key: 'share', label: 'Share of dataset' }
          ]}
        />
      </Section>

      <Section title="Network traffic features">
        <p className="muted">
          Overall averages below are taken from the exploratory analysis output generated from this dataset. Values are descriptive statistics, not attack thresholds.
        </p>
        <Table
          rows={trafficFeatures}
          columns={[
            { key: 'feature', label: 'Dataset field' },
            { key: 'meaning', label: 'Interpretation' },
            { key: 'average', label: 'Overall mean' }
          ]}
        />
      </Section>

      <Section title="How to interpret this page">
        <ul className="doc-list">
          <li><b>Normal:</b> records labelled as normal in the supplied dataset.</li>
          <li><b>Spoofing:</b> records labelled as spoofing by the dataset.</li>
          <li><b>Data Alteration:</b> records labelled as data alteration by the dataset.</li>
          <li>The category chart shows dataset label counts; it does not itself measure model accuracy.</li>
          <li>Traffic fields should be compared across categories in a follow-up analysis before claiming which features distinguish attacks.</li>
        </ul>
      </Section>
    </>
  );
}

function SimulationTable() {
  const scenarios = [
    { id: 'normal', name: 'Normal device operation', expected: 'No attack detected', description: 'Baseline trusted activity' },
    { id: 'invalid-signature', name: 'Invalid device signature', expected: 'Authentication should be rejected', description: 'Invalid signature test' },
    { id: 'abnormal-behavior', name: 'Abnormal device behavior', expected: 'Anomaly should be assessed', description: 'Unusual synthetic telemetry' },
    { id: 'suspicious-communication', name: 'Suspicious communication', expected: 'Communication risk should be assessed', description: 'Latency, jitter, or packet-loss indicators' },
    { id: 'credential-misuse', name: 'Credential misuse', expected: 'Repeated authentication failures should be flagged', description: 'Credential misuse test' },
    { id: 'tampered-firmware', name: 'Tampered firmware', expected: 'Firmware integrity issue should be flagged', description: 'Digest mismatch test' },
    { id: 'firmware-downgrade', name: 'Firmware downgrade', expected: 'Policy violation should be flagged', description: 'Version below minimum policy' },
    { id: 'combined', name: 'Combined multilayer incident', expected: 'Combined risk assessment should be produced', description: 'Evidence across multiple security layers' }
  ];

  const initialRows = () =>
    scenarios.map(s => ({
      ...s,
      status: 'Not run',
      device_id: '—',
      beforeRisk: '—',
      afterRisk: '—',
      category: '—',
      error: ''
    }));

  const [rows, setRows] = useState<any[]>(initialRows());
  const [running, setRunning] = useState('');

  async function runScenario(id: string) {
    setRunning(id);
    setRows(old => old.map(r => (r.id === id ? { ...r, status: 'Running…', error: '' } : r)));
    try {
      const response: any = await api(`/simulations/${id}`, {
        method: 'POST',
        body: JSON.stringify({ seed: 42 })
      });
      setRows(old =>
        old.map(r =>
          r.id === id
            ? {
                ...r,
                status: 'Completed',
                device_id: response.device_id || '—',
                beforeRisk: response.before?.risk_score ?? '—',
                afterRisk: response.after?.risk_score ?? '—',
                category: response.after?.risk_category || 'Unknown',
                error: ''
              }
            : r
        )
      );
    } catch (e: any) {
      setRows(old =>
        old.map(r =>
          r.id === id ? { ...r, status: 'Failed', error: e.message || 'Simulation request failed' } : r
        )
      );
    } finally {
      setRunning('');
    }
  }

  function exportRows() {
    downloadJson(
      {
        generated_at: new Date().toISOString(),
        note: 'Only rows marked Completed contain actual API simulation results. Expected outcomes are test expectations, not measured results.',
        simulations: rows
      },
      'medsecure-simulation-table.json'
    );
  }

  return (
    <>
      <PageHeader
        eyebrow="SCENARIO TESTING"
        title="Simulation table"
        subtitle="Execute a scenario through the backend and record its returned risk results. Unrun rows are not test results."
        action={
          <button className="secondary" onClick={exportRows}>
            <Download size={15} /> Export table JSON
          </button>
        }
      />

      <div className="notice">
        <FlaskConical size={16} />
        <span>
          <b>How to use:</b> Select Run for a scenario. The table records returned API results only after the simulation succeeds. A failed request is shown as Failed, not as a detection result.
        </span>
      </div>

      <Section
        title="Simulation scenarios"
        extra={
          <button className="secondary" onClick={() => setRows(initialRows())}>
            <RefreshCw size={14} /> Reset table
          </button>
        }
      >
        <Table
          rows={rows}
          columns={[
            { key: 'id', label: 'Scenario ID' },
            { key: 'name', label: 'Scenario' },
            { key: 'expected', label: 'Expected result' },
            {
              key: 'status',
              label: 'Execution status',
              render: (v: string) => (
                <Severity
                  value={v === 'Completed' ? 'Low' : v === 'Failed' ? 'High' : v === 'Running…' ? 'Medium' : 'Unknown'}
                />
              )
            },
            { key: 'device_id', label: 'Device' },
            { key: 'beforeRisk', label: 'Risk before' },
            { key: 'afterRisk', label: 'Risk after' },
            { key: 'category', label: 'Final risk category' },
            {
              key: 'action',
              label: 'Action',
              render: (_: any, r: any) => (
                <button className="secondary" disabled={!!running} onClick={() => runScenario(r.id)}>
                  <Play size={13} />
                  {running === r.id ? 'Running…' : 'Run'}
                </button>
              )
            }
          ]}
        />

        {rows.some(r => r.error) && (
          <div className="error-box" style={{ marginTop: 12 }}>
            {rows
              .filter(r => r.error)
              .map(r => `${r.name}: ${r.error}`)
              .join(' · ')}
          </div>
        )}
      </Section>

      <Section title="Reading the results">
        <ul className="doc-list">
          <li><b>Expected result</b> describes the intended test outcome; it is not proof that detection succeeded.</li>
          <li><b>Completed</b> means the backend returned a response. Review the risk values and category to interpret the result.</li>
          <li><b>Failed</b> means the request did not complete successfully; check that the backend is running and the user is authenticated.</li>
          <li>This is a synthetic academic prototype. These scenarios do not establish real-world clinical or security effectiveness.</li>
        </ul>
      </Section>
    </>
  );
}

function Research() {
  const { data, error, loading } = useApi<any>('/research/evaluation');

  return (
    <>
      <PageHeader
        eyebrow="EXPERIMENTAL EVALUATION"
        title="Research evaluation"
        subtitle="Measured metrics from a reproducible synthetic held-out dataset; results do not generalize to real deployments."
        action={
          <button className="secondary" onClick={() => window.print()}>
            <Download size={15} /> Print / save report
          </button>
        }
      />

      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorPanel error={error} />
      ) : (
        <>
          <div className="notice">
            <FlaskConical size={16} /> Seed: {data.seed} · Training samples: {data.training_samples} · Test samples: {data.test_samples} · Synthetic benchmark only.
          </div>

          <div className="metrics-grid">
            <Metric label="Precision" value={(data.precision * 100).toFixed(2) + '%'} icon={Gauge} />
            <Metric label="Recall / detection rate" value={(data.recall * 100).toFixed(2) + '%'} icon={Activity} />
            <Metric label="F1 score" value={data.f1.toFixed(4)} icon={ChartNoAxesCombined} />
            <Metric
              label="False positive rate"
              value={(data.false_positive_rate * 100).toFixed(2) + '%'}
              icon={AlertTriangle}
              tone="amber"
            />
          </div>

          <Section title="Confusion matrix">
            <div className="confusion">
              <div className="confusion-label" />
              <div>Predicted normal</div>
              <div>Predicted anomaly</div>
              <div>Actual normal</div>
              <strong>{data.true_negative} <small>TN</small></strong>
              <strong className="false-positive">{data.false_positive} <small>FP</small></strong>
              <div>Actual anomaly</div>
              <strong className="false-negative">{data.false_negative} <small>FN</small></strong>
              <strong>{data.true_positive} <small>TP</small></strong>
            </div>
          </Section>

          <Section title="Experimental method">
            <ul className="doc-list">
              <li>Isolation Forest trained on synthetic normal telemetry only.</li>
              <li>Held-out normal samples are evaluated alongside separately generated anomalous samples.</li>
              <li>Precision = TP / (TP + FP); recall = TP / (TP + FN); F1 = harmonic mean of precision and recall.</li>
              <li>False-positive rate = FP / (FP + TN); false-negative rate = FN / (FN + TP).</li>
              <li>Generated labels and patterns are simplified and do not represent validated healthcare threat distributions.</li>
            </ul>
            <button className="secondary" onClick={() => downloadJson(data, 'medsecure-research-evaluation.json')}>
              <Download size={15} /> Export JSON results
            </button>
          </Section>
        </>
      )}
    </>
  );
}

function ModelComparison() {
  // Metrics produced by ml_model/train_model.py using the same held-out test split.
  // Values are weighted averages and are shown as percentages.
  const comparison = [
    { metric: 'Accuracy', randomForest: 93.93, svm: 69.30 },
    { metric: 'Precision', randomForest: 94.32, svm: 91.15 },
    { metric: 'Recall', randomForest: 93.93, svm: 69.30 },
    { metric: 'F1 Score', randomForest: 91.65, svm: 76.63 }
  ];

  const rows = comparison.map(item => ({
    metric: item.metric,
    randomForest: `${item.randomForest.toFixed(2)}%`,
    svm: `${item.svm.toFixed(2)}%`,
    winner: item.randomForest > item.svm ? 'Random Forest' : item.svm > item.randomForest ? 'SVM' : 'Tie'
  }));

  return (
    <>
      <PageHeader
        eyebrow="MACHINE LEARNING / EXPERIMENTAL RESULTS"
        title="Model comparison"
        subtitle="Comparison of Random Forest and Support Vector Machine (SVM) on the same held-out dataset split."
        action={
          <button
            className="secondary"
            onClick={() => downloadJson({ note: 'Weighted metrics from the model training experiment; synthetic dataset only.', results: comparison }, 'random-forest-vs-svm-comparison.json')}
          >
            <Download size={15} /> Export results
          </button>
        }
      />

      <div className="notice">
        <ChartNoAxesCombined size={16} /> Values are weighted metrics from the completed training experiment. They describe this dataset split and are not evidence of real-world clinical performance.
      </div>

      <div className="metrics-grid">
        <Metric label="Best overall model" value="Random Forest" icon={ShieldCheck} tone="green" hint="Higher on all four weighted metrics" />
        <Metric label="Random Forest accuracy" value="93.93%" icon={Gauge} />
        <Metric label="SVM accuracy" value="69.30%" icon={Activity} tone="amber" />
        <Metric label="Random Forest F1 score" value="91.65%" icon={ChartNoAxesCombined} tone="green" />
      </div>

      <Section title="Performance comparison (%)">
        <div style={{ width: '100%', height: 360 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={comparison} margin={{ top: 20, right: 25, left: 10, bottom: 10 }} barGap={8} barCategoryGap="22%">
              <CartesianGrid stroke="#334155" strokeDasharray="4 4" vertical={false} />
              <XAxis dataKey="metric" tick={{ fill: '#CBD5E1', fontSize: 12 }} axisLine={{ stroke: '#475569' }} tickLine={false} />
              <YAxis domain={[0, 100]} ticks={[0, 20, 40, 60, 80, 100]} tick={{ fill: '#CBD5E1', fontSize: 12 }} axisLine={false} tickLine={false} unit="%" />
              <Tooltip
                formatter={(value: any) => [`${Number(value).toFixed(2)}%`, '']}
                contentStyle={{ backgroundColor: '#0F172A', border: '1px solid #334155', borderRadius: '10px', color: '#F8FAFC' }}
                labelStyle={{ color: '#67E8F9', fontWeight: 600 }}
              />
              <Legend wrapperStyle={{ color: '#CBD5E1', paddingTop: '12px', fontSize: '13px' }} />
              <Bar dataKey="randomForest" name="Random Forest" fill="#22D3EE" radius={[5, 5, 0, 0]} maxBarSize={48} />
              <Bar dataKey="svm" name="SVM" fill="#A78BFA" radius={[5, 5, 0, 0]} maxBarSize={48} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Section>

      <Section title="Random Forest vs SVM comparison table">
        <Table
          rows={rows}
          columns={[
            { key: 'metric', label: 'Evaluation metric' },
            { key: 'randomForest', label: 'Random Forest' },
            { key: 'svm', label: 'SVM' },
            { key: 'winner', label: 'Higher result' }
          ]}
        />
      </Section>

      <Section title="Conclusion and research note">
        <div className="success-box">
          <b>Random Forest performs better on the overall weighted metrics in this experiment.</b>
          <p>It achieved 93.93% accuracy and a 91.65% weighted F1 score, compared with 69.30% accuracy and a 76.63% weighted F1 score for SVM.</p>
        </div>
        <div className="notice" style={{ marginTop: 16 }}>
          <AlertTriangle size={16} /> Important: the class-wise results showed that Random Forest detected only about 12% of the Spoofing test examples, while SVM detected about 71%. Because the dataset is imbalanced, overall weighted metrics alone do not tell the whole story. Discuss this limitation during the demo.
        </div>
        <ul className="doc-list">
          <li>Both algorithms were evaluated using the same train/test split (80% training, 20% testing; random state 42).</li>
          <li>Precision, recall, and F1 shown here are weighted averages across the three target classes.</li>
          <li>Results are based on the current dataset and experiment configuration; they are not validated real-world healthcare security results.</li>
        </ul>
      </Section>
    </>
  );
}

function AuditPage() {
  const { data, error, loading } = useApi<any>('/audit');

  return (
    <>
      <PageHeader
        eyebrow="ACCOUNTABILITY"
        title="Audit logs"
        subtitle="Append-oriented application records for authentication, simulations, and configuration changes."
        action={
          <button className="secondary" onClick={() => data && downloadJson(data, 'medsecure-audit-log.json')}>
            <Download size={15} /> Export JSON
          </button>
        }
      />

      <div className="notice">
        <ScrollText size={16} /> These records are stored in the application database but are not cryptographically immutable or tamper-proof.
      </div>

      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorPanel error={error} />
      ) : (
        <Section title={`${data?.items?.length || 0} recent records`}>
          <Table
            rows={data?.items || []}
            columns={[
              { key: 'created_at', label: 'Timestamp', render: v => fmt(v) },
              { key: 'actor', label: 'Actor' },
              { key: 'action', label: 'Action' },
              { key: 'resource', label: 'Resource' },
              {
                key: 'outcome',
                label: 'Outcome',
                render: v => <Severity value={v === 'success' ? 'Low' : 'High'} />
              }
            ]}
          />
        </Section>
      )}
    </>
  );
}

function SettingsPage({ role }: { role: string }) {
  const { data, error, loading } = useApi<any>('/settings');

  return (
    <>
      <PageHeader
        eyebrow="POLICY CONFIGURATION"
        title="Settings"
        subtitle="Review prototype thresholds and risk assumptions. Administrator-only changes are enforced by the backend."
      />

      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorPanel error={error} />
      ) : (
        <>
          <Section title="Risk engine weights">
            <p className="muted">Weights must total 100%. Current default values are prototype assumptions.</p>
            <Table
              rows={Object.entries(data.risk_weights || {}).map(([layer, weight]) => ({ layer, weight: `${weight}%` }))}
              columns={[
                { key: 'layer', label: 'Security layer' },
                { key: 'weight', label: 'Weight' }
              ]}
            />
          </Section>

          <Section title="Detection thresholds">
            <Table
              rows={Object.entries(data.communication || {}).map(([key, value]) => ({ key, value }))}
              columns={[
                { key: 'key', label: 'Communication threshold' },
                { key: 'value', label: 'Value' }
              ]}
            />
            <Table
              rows={Object.entries(data.credentials || {}).map(([key, value]) => ({ key, value }))}
              columns={[
                { key: 'key', label: 'Credential threshold' },
                { key: 'value', label: 'Value' }
              ]}
            />
            <div className="setting-row">
              <span>Minimum firmware version</span>
              <b>{data.minimum_firmware_version}</b>
            </div>
            <div className="setting-row">
              <span>Low evidence coverage alert</span>
              <b>{data.low_coverage_alert_pct}%</b>
            </div>
            {role !== 'administrator' && (
              <p className="muted">You are signed in as an analyst. Only administrators may modify settings.</p>
            )}
          </Section>
        </>
      )}
    </>
  );
}

function About() {
  const layers = [
    ['Cryptographic authentication', 'RSA-PSS / SHA-256 challenge-response'],
    ['Behavioral AI', 'Isolation Forest synthetic telemetry inference'],
    ['Communication monitoring', 'Transparent statistical anomaly rules'],
    ['Credential misuse', 'Threshold-based suspicious pattern detection'],
    ['Firmware integrity', 'SHA-256 comparison and version policy']
  ];

  return (
    <>
      <PageHeader
        eyebrow="PROJECT INFORMATION"
        title="About MedSecure Sentinel"
        subtitle="A software-only academic prototype for studying multilayer security in simulated healthcare IoT environments."
      />

      <Section title="Official project title">
        <h2 className="official-title">
          A Hybrid Multilayer Cybersecurity Framework for Secure and Resilient IoT Ecosystems
        </h2>
        <p className="muted">Intelligent Security for Resilient IoT Ecosystems</p>
      </Section>

      <div className="two-col">
        <Section title="Security layers">
          <div className="security-list">
            {layers.map(([a, b]) => (
              <div key={a}>
                <ShieldCheck />
                <span>
                  <b>{a}</b>
                  <small>{b}</small>
                </span>
              </div>
            ))}
          </div>
        </Section>

        <Section title="Important limitations">
          <ul className="doc-list">
            <li>All devices, network addresses, and security scenarios are synthetic.</li>
            <li>Risk weights and thresholds are configurable prototype assumptions, not calibrated probabilities.</li>
            <li>MITM-like indicators are not proof of interception.</li>
            <li>No clinical effectiveness or real-world hospital deployment is claimed.</li>
            <li>Local demo device keys are for educational simulation, not production use.</li>
          </ul>
        </Section>
      </div>
    </>
  );
}

export default App;
