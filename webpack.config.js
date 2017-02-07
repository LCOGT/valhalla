var path = require('path');
var BundleTracker = require('webpack-bundle-tracker');

module.exports = {
  entry: {
    compose: './static/js/compose',
  },
  output: {
    path: path.resolve('./static/bundles/'),
    filename: '[name].js',
  },
  module: {
    rules: [
      {
        test: /\.vue$/,
        loader: 'vue-loader',
        options: {
          loaders: {
            // Since sass-loader (weirdly) has SCSS as its default parse mode, we map
            // the "scss" and "sass" values for the lang attribute to the right configs here.
            // other preprocessors should work out of the box, no loader config like this nessessary.
            'scss': 'vue-style-loader!css-loader!sass-loader',
            'sass': 'vue-style-loader!css-loader!sass-loader?indentedSyntax'
          }
          // other vue-loader options go here
        }
      },
      {
        test: /\.js$/,
        loader: 'babel-loader',
        exclude: /node_modules/
      },
      {
        test: /\.css$/,
        use: [ 'style-loader', 'css-loader' ]
      }
    ]
  },
  resolve: {
    alias: {
      'vue$': 'vue/dist/vue.common.js',
      'jquery': path.join(__dirname, 'node_modules/jquery/src/jquery')
    }
  },

  plugins: [
    new BundleTracker({filename: './webpack-stats.json'}),
  ],
};