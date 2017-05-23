module.exports = {
  'env': {
    'browser': true,
    'es6': true,
  },
  'extends': 'airbnb',
  'rules': {
    'guard-for-in': 'off',
    'no-alert': 'off',
    'no-param-reassign': 'off',
    'no-restricted-syntax': 'off',
  },
  'globals': {
    '$': true,
    'Highcharts': true,
  },
};
