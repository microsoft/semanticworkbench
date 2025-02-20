import typescriptEslint from '@typescript-eslint/eslint-plugin';
import tsParser from '@typescript-eslint/parser';
import importPlugin from 'eslint-plugin-import';

export default [
    {
        files: ['**/*.ts'],
    },
    {
        ignorePatterns: ['dist', '.*.js', '*.config.js', 'node_modules'],

        plugins: {
            '@typescript-eslint': typescriptEslint,
            import: importPlugin,
        },

        languageOptions: {
            parser: tsParser,
            ecmaVersion: 2022,
            sourceType: 'module',
        },

        rules: {
            '@typescript-eslint/naming-convention': [
                'warn',
                {
                    selector: 'import',
                    format: ['camelCase', 'PascalCase'],
                },
            ],
            '@typescript-eslint/brace-style': ['off'],
            '@typescript-eslint/space-before-function-paren': [
                'error',
                { anonymous: 'always', named: 'never', asyncArrow: 'always' },
            ],
            '@typescript-eslint/semi': ['error', 'always'],
            '@typescript-eslint/triple-slash-reference': ['error', { types: 'prefer-import' }],
            '@typescript-eslint/indent': ['off'],
            '@typescript-eslint/comma-dangle': ['error', 'always-multiline'],
            '@typescript-eslint/strict-boolean-expressions': 'off',
            '@typescript-eslint/member-delimiter-style': [
                'error',
                {
                    multiline: {
                        delimiter: 'semi',
                        requireLast: true,
                    },
                    singleline: {
                        delimiter: 'semi',
                        requireLast: false,
                    },
                },
            ],
            '@typescript-eslint/explicit-function-return-type': 'off',
        },
    },
];
