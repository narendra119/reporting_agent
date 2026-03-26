import { useState, useRef } from 'react';
import {
  BarChart, Bar,
  LineChart, Line,
  AreaChart, Area,
  ScatterChart, Scatter, ZAxis,
  PieChart, Pie,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

// --- Utilities ---

const formatTick = (val) => {
  if (typeof val !== 'string') return val;
  // Format YYYY-MM or YYYY-MM-DD into "Jan '24"
  if (/^\d{4}-\d{2}(-\d{2})?$/.test(val)) {
    const d = new Date(val.length === 7 ? val + '-01' : val);
    if (!isNaN(d)) return d.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
  }
  return val;
};

const exportCSV = (data) => {
  const cols = Object.keys(data[0]);
  const rows = data.map(row => cols.map(c => JSON.stringify(row[c] ?? '')).join(','));
  const csv = [cols.join(','), ...rows].join('\n');
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
  a.download = 'report.csv';
  a.click();
};

const exportChartPNG = (ref) => {
  const svg = ref.current?.querySelector('svg');
  if (!svg) return;
  const { width, height } = svg.getBoundingClientRect();
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, width, height);
  const url = URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(svg)], { type: 'image/svg+xml' }));
  const img = new Image();
  img.onload = () => {
    ctx.drawImage(img, 0, 0);
    URL.revokeObjectURL(url);
    const a = document.createElement('a');
    a.download = 'chart.png';
    a.href = canvas.toDataURL('image/png');
    a.click();
  };
  img.src = url;
};

const HISTORY_KEY = 'reporting_agent_history';
const loadHistory = () => { try { return JSON.parse(localStorage.getItem(HISTORY_KEY)) || []; } catch { return []; } };
const saveHistory = (h) => localStorage.setItem(HISTORY_KEY, JSON.stringify(h));

// --- Skeleton ---

const Skeleton = () => (
  <div style={{ padding: '16px 0' }}>
    <style>{`@keyframes shimmer { 0%,100%{opacity:.4} 50%{opacity:.9} }`}</style>
    {[75, 55, 85, 45, 65].map((w, i) => (
      <div key={i} style={{ display: 'flex', alignItems: 'flex-end', gap: '10px', marginBottom: '10px' }}>
        <div style={{ ...styles.skelBlock, width: '36px', height: '13px' }} />
        <div style={{ ...styles.skelBlock, height: `${w * 2.8}px`, width: `${w}%` }} />
      </div>
    ))}
  </div>
);

// --- Chart Components ---

const tooltipStyle = { borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' };

const BarChartView = ({ data, onDrillDown }) => {
  const keys = Object.keys(data[0]).filter(k => k !== 'name');
  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={data} onClick={e => e?.activeLabel && onDrillDown?.(e.activeLabel)}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="name" axisLine={false} tickLine={false} tickFormatter={formatTick} />
        <YAxis axisLine={false} tickLine={false} />
        <Tooltip contentStyle={tooltipStyle} />
        <Legend />
        {keys.map((key, i) => (
          <Bar key={key} dataKey={key} fill={COLORS[i % COLORS.length]} radius={[4, 4, 0, 0]} cursor="pointer" />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
};

const LineChartView = ({ data }) => {
  const keys = Object.keys(data[0]).filter(k => k !== 'name');
  return (
    <ResponsiveContainer width="100%" height={320}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="name" axisLine={false} tickLine={false} tickFormatter={formatTick} />
        <YAxis axisLine={false} tickLine={false} />
        <Tooltip contentStyle={tooltipStyle} />
        <Legend />
        {keys.map((key, i) => (
          <Line key={key} type="monotone" dataKey={key} stroke={COLORS[i % COLORS.length]} strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
};

const AreaChartView = ({ data }) => {
  const keys = Object.keys(data[0]).filter(k => k !== 'name');
  return (
    <ResponsiveContainer width="100%" height={320}>
      <AreaChart data={data}>
        <defs>
          {keys.map((key, i) => (
            <linearGradient key={key} id={`grad-${key}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={COLORS[i % COLORS.length]} stopOpacity={0.2} />
              <stop offset="95%" stopColor={COLORS[i % COLORS.length]} stopOpacity={0} />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="name" axisLine={false} tickLine={false} tickFormatter={formatTick} />
        <YAxis axisLine={false} tickLine={false} />
        <Tooltip contentStyle={tooltipStyle} />
        <Legend />
        {keys.map((key, i) => (
          <Area key={key} type="monotone" dataKey={key} stroke={COLORS[i % COLORS.length]} strokeWidth={2} fill={`url(#grad-${key})`} />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );
};

const PieChartView = ({ data, onDrillDown }) => (
  <ResponsiveContainer width="100%" height={320}>
    <PieChart>
      <Pie
        data={data.map((entry, i) => ({ ...entry, fill: COLORS[i % COLORS.length] }))}
        dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={130} label
        onClick={e => e?.name && onDrillDown?.(e.name)} cursor="pointer"
      />
      <Tooltip />
      <Legend />
    </PieChart>
  </ResponsiveContainer>
);

const DonutChartView = ({ data, onDrillDown }) => (
  <ResponsiveContainer width="100%" height={320}>
    <PieChart>
      <Pie
        data={data.map((entry, i) => ({ ...entry, fill: COLORS[i % COLORS.length] }))}
        dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={80} outerRadius={130} label
        onClick={e => e?.name && onDrillDown?.(e.name)} cursor="pointer"
      />
      <Tooltip />
      <Legend />
    </PieChart>
  </ResponsiveContainer>
);

// Expected data shape: [{ x, y, name? }]
const ScatterChartView = ({ data }) => (
  <ResponsiveContainer width="100%" height={320}>
    <ScatterChart>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="x" name="x" axisLine={false} tickLine={false} />
      <YAxis dataKey="y" name="y" axisLine={false} tickLine={false} />
      <ZAxis range={[60, 60]} />
      <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={tooltipStyle} />
      <Scatter data={data} fill={COLORS[0]} />
    </ScatterChart>
  </ResponsiveContainer>
);

// Expected data shape: [{ row, col, value }]
const HeatmapView = ({ data }) => {
  const rows = [...new Set(data.map(d => d.row))];
  const cols = [...new Set(data.map(d => d.col))];
  const max = Math.max(...data.map(d => d.value));
  const lookup = Object.fromEntries(data.map(d => [`${d.row}|${d.col}`, d.value]));
  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ borderCollapse: 'separate', borderSpacing: '3px', fontSize: '12px' }}>
        <thead>
          <tr>
            <th style={{ padding: '4px 8px' }} />
            {cols.map(col => <th key={col} style={{ padding: '4px 8px', color: '#6b7280', fontWeight: 500, whiteSpace: 'nowrap' }}>{col}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map(row => (
            <tr key={row}>
              <td style={{ padding: '4px 8px', color: '#6b7280', fontWeight: 500, whiteSpace: 'nowrap' }}>{row}</td>
              {cols.map(col => {
                const val = lookup[`${row}|${col}`] ?? 0;
                const intensity = max > 0 ? val / max : 0;
                return (
                  <td key={col} title={`${row}, ${col}: ${val}`} style={{
                    width: '44px', height: '38px', textAlign: 'center', borderRadius: '4px',
                    backgroundColor: `rgba(59,130,246,${0.08 + intensity * 0.82})`,
                    color: intensity > 0.6 ? '#fff' : '#374151', fontWeight: 500,
                  }}>
                    {val}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// Expected data shape: [{ label, value, change? }]
const MetricCardsView = ({ data }) => (
  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '16px', padding: '8px 0' }}>
    {data.map((item, i) => {
      const isPos = item.change?.startsWith('+');
      const isNeg = item.change?.startsWith('-');
      return (
        <div key={i} style={styles.metricCard}>
          <p style={styles.metricLabel}>{item.label}</p>
          <p style={styles.metricValue}>{item.value}</p>
          {item.change && (
            <p style={{ ...styles.metricChange, color: isPos ? '#10b981' : isNeg ? '#ef4444' : '#6b7280' }}>
              {item.change}
            </p>
          )}
        </div>
      );
    })}
  </div>
);

const TableView = ({ data }) => {
  const columns = Object.keys(data[0]);
  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
        <thead>
          <tr>{columns.map(col => <th key={col} style={styles.th}>{col}</th>)}</tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={i} style={{ backgroundColor: i % 2 === 0 ? '#fff' : '#f9fafb' }}>
              {columns.map(col => <td key={col} style={styles.td}>{row[col]}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// --- Main Component ---

const ReportingDashboard = () => {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState(loadHistory);
  // streamLog: [{type:'text', content:''} | {type:'tool', name, input, result, done}]
  const [streamLog, setStreamLog] = useState([]);
  const [streamExpanded, setStreamExpanded] = useState(false);
  const streamBodyRef = useRef(null);
  const chartRef = useRef(null);

  const submitQuery = async (q) => {
    if (!q.trim()) return;
    setQuery(q);
    setIsLoading(true);
    setError(null);
    setResult(null);
    setStreamLog([]);
    setStreamExpanded(true);

    try {
      const response = await fetch('http://localhost:8000/api/report/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q }),
      });
      if (!response.ok) throw new Error(`Server error: ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const frames = buffer.split('\n\n');
        buffer = frames.pop(); // keep incomplete trailing frame

        for (const frame of frames) {
          const lines = frame.split('\n');
          const eventLine = lines.find(l => l.startsWith('event:'));
          const dataLine  = lines.find(l => l.startsWith('data:'));
          if (!eventLine || !dataLine) continue;

          const type    = eventLine.replace('event:', '').trim();
          const payload = JSON.parse(dataLine.replace('data:', '').trim());

          if (type === 'text') {
            setStreamLog(prev => {
              const last = prev[prev.length - 1];
              const updated = last?.type === 'text'
                ? [...prev.slice(0, -1), { type: 'text', content: last.content + payload.chunk }]
                : [...prev, { type: 'text', content: payload.chunk }];
              requestAnimationFrame(() => {
                if (streamBodyRef.current) streamBodyRef.current.scrollTop = streamBodyRef.current.scrollHeight;
              });
              return updated;
            });
          }
          if (type === 'tool_call') {
            setStreamLog(prev => [...prev, { type: 'tool', name: payload.name, input: payload.input, result: null, done: false }]);
          }
          if (type === 'tool_result') {
            setStreamLog(prev => {
              const idx = [...prev].reverse().findIndex(e => e.type === 'tool' && e.name === payload.name && !e.done);
              if (idx === -1) return prev;
              const realIdx = prev.length - 1 - idx;
              const updated = [...prev];
              updated[realIdx] = { ...updated[realIdx], result: payload.result, done: true };
              return updated;
            });
          }
          if (type === 'done') {
            setStreamExpanded(false);
            setResult(payload);
            setHistory(prev => {
              const updated = [q, ...prev.filter(h => h !== q)].slice(0, 10);
              saveHistory(updated);
              return updated;
            });
          }
          if (type === 'error') throw new Error(payload.message);
        }
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDrillDown = (label) => submitQuery(`${query} — breakdown by ${label}`);

  const handleExport = () => {
    if (!result) return;
    result.type === 'table' ? exportCSV(result.data) : exportChartPNG(chartRef);
  };

  const renderContent = () => {
    if (isLoading) return <Skeleton />;
    if (error) return (
      <div style={styles.placeholder}>
        <div style={{ textAlign: 'center' }}>
          <p style={{ color: '#ef4444', marginBottom: '12px' }}>Error: {error}</p>
          <button onClick={() => submitQuery(query)} style={styles.retryBtn}>Try again</button>
        </div>
      </div>
    );
    if (!result) return <div style={styles.placeholder}>Results will appear here</div>;

    const { type, data } = result;
    if (!data || data.length === 0) return <div style={styles.placeholder}>No data returned.</div>;

    switch (type) {
      case 'bar':     return <BarChartView data={data} onDrillDown={handleDrillDown} />;
      case 'line':    return <LineChartView data={data} />;
      case 'area':    return <AreaChartView data={data} />;
      case 'pie':     return <PieChartView data={data} onDrillDown={handleDrillDown} />;
      case 'donut':   return <DonutChartView data={data} onDrillDown={handleDrillDown} />;
      case 'scatter': return <ScatterChartView data={data} />;
      case 'heatmap': return <HeatmapView data={data} />;
      case 'metric':  return <MetricCardsView data={data} />;
      case 'table':   return <TableView data={data} />;
      default:        return <div style={{ ...styles.placeholder, color: '#ef4444' }}>Unknown type: "{type}"</div>;
    }
  };

  const canExport = result && !isLoading;
  const isChartType = result && !['table', 'metric'].includes(result.type);

  return (
    <div style={styles.page}>
      <h1 style={styles.heading}>Reporting Agent</h1>

      {/* Query input */}
      <form onSubmit={e => { e.preventDefault(); submitQuery(query); }} style={styles.form}>
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Ask a question about your data..."
          disabled={isLoading}
          style={styles.input}
        />
        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          style={{
            ...styles.button,
            backgroundColor: isLoading || !query.trim() ? '#93c5fd' : '#3b82f6',
            cursor: isLoading || !query.trim() ? 'not-allowed' : 'pointer',
          }}
        >
          {isLoading ? 'Analyzing...' : 'Ask'}
        </button>
      </form>

      {/* Query history chips */}
      {history.length > 0 && (
        <div style={styles.historyRow}>
          {history.map((h, i) => (
            <button key={i} onClick={() => submitQuery(h)} style={styles.historyChip} title={h}>
              {h.length > 42 ? h.slice(0, 42) + '…' : h}
            </button>
          ))}
        </div>
      )}

      {/* Live stream panel */}
      {streamLog.length > 0 && (() => {
        const toolCount  = streamLog.filter(e => e.type === 'tool').length;
        const charCount  = streamLog.filter(e => e.type === 'text').reduce((a, e) => a + e.content.length, 0);
        const summary    = [toolCount > 0 && `${toolCount} tool call${toolCount > 1 ? 's' : ''}`, charCount > 0 && `${charCount} chars`].filter(Boolean).join(' · ');
        return (
          <div style={styles.streamPanel}>
            <div style={styles.streamHeader} onClick={() => setStreamExpanded(e => !e)}>
              <span style={styles.streamTitle}>
                {isLoading && <span style={styles.streamDot} />}
                Agent Reasoning
              </span>
              {!streamExpanded && <span style={styles.streamSummary}>{summary}</span>}
              <span style={styles.streamToggle}>{streamExpanded ? '▲' : '▼'}</span>
            </div>
            {streamExpanded && (
              <div ref={streamBodyRef} style={styles.streamBody}>
                {streamLog.map((entry, i) => {
                  if (entry.type === 'text') return (
                    <p key={i} style={styles.streamText}>{entry.content}</p>
                  );
                  if (entry.type === 'tool') return (
                    <div key={i} style={styles.toolBlock}>
                      <div style={styles.toolHeader}>
                        <span style={{ ...styles.toolBadge, opacity: entry.done ? 0.7 : 1 }}>
                          {entry.done ? '✓' : '⟳'} {entry.name}
                        </span>
                        <code style={styles.toolInput}>{JSON.stringify(entry.input)}</code>
                      </div>
                      {entry.done && entry.result && (
                        <pre style={styles.toolResult}>
                          {entry.result.length > 400 ? entry.result.slice(0, 400) + '\n…' : entry.result}
                        </pre>
                      )}
                    </div>
                  );
                  return null;
                })}
              </div>
            )}
          </div>
        );
      })()}

      {/* Result card */}
      <div style={styles.card}>
        {result && (
          <div style={styles.cardHeader}>
            <div>
              {result.title && <h2 style={styles.cardTitle}>{result.title}</h2>}
              <p style={styles.queryLabel}>{query}</p>
            </div>
            {canExport && (
              <button onClick={handleExport} style={styles.exportBtn}>
                {isChartType ? '↓ PNG' : '↓ CSV'}
              </button>
            )}
          </div>
        )}

        <div ref={chartRef}>
          {renderContent()}
        </div>

        {result?.insights && (
          <p style={styles.summary}>{result.insights}</p>
        )}
      </div>
    </div>
  );
};

const styles = {
  page: {
    maxWidth: '900px',
    margin: '40px auto',
    padding: '0 20px',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  },
  heading: { fontSize: '22px', fontWeight: 700, marginBottom: '20px', color: '#111827' },
  form: { display: 'flex', gap: '8px', marginBottom: '12px' },
  input: {
    flex: 1, padding: '10px 14px', fontSize: '15px',
    border: '1px solid #d1d5db', borderRadius: '8px', outline: 'none',
  },
  button: { padding: '10px 22px', fontSize: '15px', fontWeight: 600, color: '#fff', border: 'none', borderRadius: '8px' },
  historyRow: { display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '16px' },
  historyChip: {
    padding: '4px 10px', fontSize: '12px', color: '#374151',
    backgroundColor: '#f3f4f6', border: '1px solid #e5e7eb',
    borderRadius: '999px', cursor: 'pointer', whiteSpace: 'nowrap',
  },
  card: {
    minHeight: '420px', border: '1px solid #e5e7eb', borderRadius: '12px',
    padding: '24px', backgroundColor: '#fff', boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.08)',
  },
  cardHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' },
  cardTitle: { fontSize: '16px', fontWeight: 700, color: '#111827', margin: '0 0 2px 0' },
  queryLabel: { fontSize: '13px', color: '#6b7280', margin: 0 },
  exportBtn: {
    padding: '6px 12px', fontSize: '12px', fontWeight: 600, color: '#374151',
    backgroundColor: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '6px',
    cursor: 'pointer', whiteSpace: 'nowrap',
  },
  placeholder: {
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    height: '360px', color: '#9ca3af', fontSize: '15px',
  },
  summary: {
    marginTop: '16px', padding: '12px 16px', backgroundColor: '#f0f9ff',
    borderLeft: '3px solid #3b82f6', borderRadius: '0 6px 6px 0',
    fontSize: '14px', color: '#1e40af', lineHeight: 1.6,
  },
  retryBtn: {
    padding: '8px 18px', fontSize: '14px', fontWeight: 600,
    color: '#fff', backgroundColor: '#3b82f6', border: 'none', borderRadius: '6px', cursor: 'pointer',
  },
  skelBlock: { backgroundColor: '#e5e7eb', borderRadius: '4px', animation: 'shimmer 1.4s ease-in-out infinite' },
  streamPanel: {
    marginBottom: '16px', border: '1px solid #e5e7eb', borderRadius: '10px',
    backgroundColor: '#f8fafc', overflow: 'hidden',
  },
  streamHeader: {
    display: 'flex', alignItems: 'center', gap: '8px',
    padding: '8px 14px', cursor: 'pointer', userSelect: 'none',
    borderBottom: '1px solid transparent',
  },
  streamTitle: {
    display: 'flex', alignItems: 'center', gap: '6px',
    fontSize: '11px', fontWeight: 600, color: '#6b7280',
    letterSpacing: '0.05em', textTransform: 'uppercase',
  },
  streamSummary: { fontSize: '11px', color: '#9ca3af', flex: 1 },
  streamToggle: { fontSize: '10px', color: '#9ca3af', marginLeft: 'auto' },
  streamDot: {
    display: 'inline-block', width: '7px', height: '7px', borderRadius: '50%',
    backgroundColor: '#10b981', animation: 'shimmer 1.2s ease-in-out infinite',
  },
  streamBody: {
    padding: '12px 14px', maxHeight: '280px', overflowY: 'auto',
    borderTop: '1px solid #e5e7eb',
  },
  streamText: {
    margin: '0 0 8px 0', fontSize: '13px', lineHeight: 1.7, color: '#374151',
    whiteSpace: 'pre-wrap', wordBreak: 'break-word',
  },
  toolBlock: {
    margin: '6px 0', borderRadius: '6px', border: '1px solid #e5e7eb',
    backgroundColor: '#fff', overflow: 'hidden',
  },
  toolHeader: {
    display: 'flex', alignItems: 'center', gap: '8px',
    padding: '6px 10px', flexWrap: 'wrap',
  },
  toolBadge: {
    fontSize: '11px', fontWeight: 600, padding: '2px 8px',
    backgroundColor: '#eff6ff', color: '#3b82f6',
    borderRadius: '999px', whiteSpace: 'nowrap',
  },
  toolInput: {
    fontSize: '11px', color: '#6b7280', flex: 1,
    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
  },
  toolResult: {
    margin: 0, padding: '6px 10px',
    fontSize: '11px', color: '#374151', lineHeight: 1.5,
    whiteSpace: 'pre-wrap', wordBreak: 'break-word',
    borderTop: '1px solid #f3f4f6', backgroundColor: '#fafafa',
    maxHeight: '120px', overflowY: 'auto',
  },
  th: { textAlign: 'left', padding: '10px 12px', borderBottom: '2px solid #e5e7eb', color: '#6b7280', fontWeight: 600, whiteSpace: 'nowrap' },
  td: { padding: '10px 12px', borderBottom: '1px solid #e5e7eb', color: '#374151' },
  metricCard: { padding: '20px', border: '1px solid #e5e7eb', borderRadius: '10px', backgroundColor: '#f9fafb' },
  metricLabel: { fontSize: '13px', color: '#6b7280', margin: '0 0 6px 0', fontWeight: 500 },
  metricValue: { fontSize: '26px', fontWeight: 700, color: '#111827', margin: '0 0 4px 0' },
  metricChange: { fontSize: '13px', fontWeight: 500, margin: 0 },
};

export default ReportingDashboard;
