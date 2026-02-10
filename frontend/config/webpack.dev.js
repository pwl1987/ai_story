const { merge } = require('webpack-merge');
const common = require('./webpack.common.js');

module.exports = merge(common, {
  mode: 'development',
  devtool: 'eval-source-map',
  devServer: {
    host: '0.0.0.0',  // 允许局域网访问
    port: 3000,
    hot: true,
    open: true,
    historyApiFallback: true,
    client: {
      overlay: {
        errors: true,
        warnings: false,
      },
    },
    proxy: {
      '/api': {
        target: 'http://10.30.5.62:8000',
        changeOrigin: true,
        secure: false,
        logLevel: 'debug',
      },
      '/media': {
        target: 'http://10.30.5.62:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
