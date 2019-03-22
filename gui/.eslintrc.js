module.exports = {
    root: true,
    parser: 'babel-eslint',
    parserOptions: {
        sourceType: 'module',
    },
    env: {
        browser: true,
        node: true,
    },
    extends: 'airbnb-base',
    globals: {
        __static: true,
    },
    plugins: ['html'],
    rules: {
        'global-require': 0,
        'import/no-unresolved': 0,
        'no-param-reassign': 0,
        'no-shadow': 0,
        'import/extensions': 0,
        'import/newline-after-import': 0,
        'no-multi-assign': 0,
        // allow debugger during development
        'no-debugger': process.env.NODE_ENV === 'production' ? 2 : 0,
        'arrow-parens': ['error', 'as-needed'],
        'prefer-destructuring': 'off',
        'indent': ['error', 4, { SwitchCase: 1 }],
        'no-else-return': 'off',
        'no-plusplus': 'off',
        'function-paren-newline': 'off',
        'no-bitwise': 'off',
        'no-mixed-operators': 'off',
        'no-underscore-dangle': 'off',
        'import/prefer-default-export': 'off',
        'no-restricted-syntax': 0,
        'no-alert': 0,
    },
};