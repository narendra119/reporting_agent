import { useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie,
} from 'recharts';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

// --- Chart Components ---

const BarChartView = ({ data }) => {
  const keys = Object.keys(data[0]).filter(k => k !== 'name');
  return (
    <ResponsiveContainer width="100%" height={340}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="name" axisLine={false} tickLine={false} />
        <YAxis axisLine={false} tickLine={false} />
        <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
        <Legend />
        {keys.map((key, i) => (
          <Bar key={key} dataKey={key} fill={COLORS[i % COLORS.length]} radius={[4, 4, 0, 0]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
};

const PieChartView = ({ data }) => (
  <ResponsiveContainer width="100%" height={340}>
    <PieChart>
      <Pie
        data={data.map((entry, i) => ({ ...entry, fill: COLORS[i % COLORS.length] }))}
        dataKey="value"
        nameKey="name"
        cx="50%"
        cy="50%"
        outerRadius={130}
        label
      />
      <Tooltip />
      <Legend />
    </PieChart>
  </ResponsiveContainer>
);

const TableView = ({ data }) => {
  const columns = Object.keys(data[0]);
  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
        <thead>
          <tr>
            {columns.map(col => (
              <th key={col} style={styles.th}>{col}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={i} style={{ backgroundColor: i % 2 === 0 ? '#fff' : '#f9fafb' }}>
              {columns.map(col => (
                <td key={col} style={styles.td}>{row[col]}</td>
              ))}
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch('http://localhost:8000/api/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });
      if (!response.ok) throw new Error(`Server error: ${response.status}`);
      setResult(await response.json());
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const renderContent = () => {
    if (isLoading) {
      return <div style={styles.placeholder}>Agent is analyzing data...</div>;
    }
    if (error) {
      return <div style={{ ...styles.placeholder, color: '#ef4444' }}>Error: {error}</div>;
    }
    if (!result) {
      return <div style={styles.placeholder}>Results will appear here</div>;
    }

    const { type, data } = result;

    if (!data || data.length === 0) {
      return <div style={styles.placeholder}>No data returned.</div>;
    }

    switch (type) {
      case 'bar': return <BarChartView data={data} />;
      case 'pie': return <PieChartView data={data} />;
      case 'table': return <TableView data={data} />;
      default:    return <div style={{ ...styles.placeholder, color: '#ef4444' }}>Unknown type: "{type}"</div>;
    }
  };

  return (
    <div style={styles.page}>
      <h1 style={styles.heading}>Reporting Agent</h1>

      {/* Query input */}
      <form onSubmit={handleSubmit} style={styles.form}>
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

      {/* Result container */}
      <div style={styles.card}>
        {result && (
          <p style={styles.queryLabel}>{query}</p>
        )}
        {renderContent()}
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
  heading: {
    fontSize: '22px',
    fontWeight: 700,
    marginBottom: '20px',
    color: '#111827',
  },
  form: {
    display: 'flex',
    gap: '8px',
    marginBottom: '20px',
  },
  input: {
    flex: 1,
    padding: '10px 14px',
    fontSize: '15px',
    border: '1px solid #d1d5db',
    borderRadius: '8px',
    outline: 'none',
  },
  button: {
    padding: '10px 22px',
    fontSize: '15px',
    fontWeight: 600,
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
  },
  card: {
    minHeight: '420px',
    border: '1px solid #e5e7eb',
    borderRadius: '12px',
    padding: '24px',
    backgroundColor: '#fff',
    boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.08)',
  },
  placeholder: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '360px',
    color: '#9ca3af',
    fontSize: '15px',
  },
  queryLabel: {
    fontSize: '14px',
    fontWeight: 600,
    color: '#6b7280',
    marginBottom: '16px',
    marginTop: 0,
  },
  th: {
    textAlign: 'left',
    padding: '10px 12px',
    borderBottom: '2px solid #e5e7eb',
    color: '#6b7280',
    fontWeight: 600,
    whiteSpace: 'nowrap',
  },
  td: {
    padding: '10px 12px',
    borderBottom: '1px solid #e5e7eb',
    color: '#374151',
  },
};

export default ReportingDashboard;
