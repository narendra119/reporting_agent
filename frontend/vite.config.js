import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  esbuild: {
    // This tells Vite to treat .js files as JSX
    loader: 'jsx',
    include: /src\/.*\.js$|node_modules\/.*\.js$|.\/main\.js$|.\/index\.js$|.\/ReportingDashboard\.js$/,
  },
  optimizeDeps: {
    esbuildOptions: {
      loader: {
        '.js': 'jsx',
      },
    },
  },
})