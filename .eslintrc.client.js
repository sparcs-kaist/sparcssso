module.exports = {
  'env': {
    'browser': true,
  },
  'extends': 'es5',
  'plugins': [
    'html',
  ],
  'rules': {
    'comma-dangle': ['error', 'always'],
    'func-names': 'off',
    'no-constant-condition': 'off',
  },
  'globals': {
    '$': true,
    'grecaptcha': true,
  },
  'settings': {
    'html/indent': '+0',
    'html/report-bad-indent': 'error',
  },
};
