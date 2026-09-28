import { defineConfig } from '#q-app';

export default defineConfig(() => {
  return {
    boot: ['api', 'session'],
    extras: ['roboto-font', 'material-icons'],
    build: {
      typescript: {
        strict: true,
        vueShim: true,
      },
      vueRouterMode: 'history',
    },
    devServer: {
      host: '0.0.0.0',
      port: 9000,
      open: false,
      proxy: {
        '/api': { target: 'http://127.0.0.1:8000', changeOrigin: false },
        '/media': { target: 'http://127.0.0.1:8000', changeOrigin: false },
        '/admin': { target: 'http://127.0.0.1:8000', changeOrigin: false },
        '/static': { target: 'http://127.0.0.1:8000', changeOrigin: false },
      },
    },
    framework: {
      plugins: ['Notify', 'Dialog', 'Loading'],
    },
    animations: [],
  };
});
