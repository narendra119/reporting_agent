import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, ResponsiveContainer 
} from 'recharts';

// 1. Logic to fetch data from your Python (FastAPI/Flask) backend
const fetchReportData = async () => {
  const response = await fetch('http://localhost:8000/api/report');
  if (!response.ok) throw new Error('Network response was not ok');
  return response.json(); // Expected: [{ name: 'A', value: 10 }, ...]
};

const ReportingDashboard = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['reportData'],
    queryFn: fetchReportData,
  });

  // 2. Handle the "Loading" state for the Agent
  if (isLoading) return <div className="p-8 text-center">Agent is analyzing data...</div>;

  // 3. Handle potential SQL or Connection errors
  if (error) return <div className="p-8 text-red-500">Error: {error.message}</div>;

  return (
    <div className="w-full h-[400px] p-4 bg-white rounded-lg shadow-sm">
      <h2 className="text-xl font-bold mb-4">Agent Analysis Result</h2>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis 
            dataKey="name" 
            axisLine={false} 
            tickLine={false} 
          />
          <YAxis axisLine={false} tickLine={false} />
          <Tooltip 
            cursor={{ fill: '#f3f4f6' }}
            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
          />
          <Legend />
          {/* The dataKey must match the keys returned by your Python dicts */}
          <Bar dataKey="revenue" fill="#3b82f6" radius={[4, 4, 0, 0]} />
          <Bar dataKey="orders" fill="#10b981" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ReportingDashboard;