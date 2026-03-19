import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ReportingDashboard from './ReportingDashboard'; // or wherever your code is

const queryClient = new QueryClient();

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ReportingDashboard />
    </QueryClientProvider>
  </React.StrictMode>
);