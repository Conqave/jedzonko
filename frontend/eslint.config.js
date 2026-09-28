import js from '@eslint/js';
import globals from 'globals';
import pluginVue from 'eslint-plugin-vue';
import pluginQuasar from '@quasar/app-vite/eslint';
import { defineConfigWithVueTs, vueTsConfigs } from '@vue/eslint-config-typescript';
import prettierSkipFormatting from '@vue/eslint-config-prettier/skip-formatting';

const noComments = {
  meta: { type: 'problem', schema: [] },
  create(context) {
    const sourceCode = context.sourceCode;
    return {
      Program(node) {
        for (const comment of sourceCode.getAllComments()) {
          context.report({ loc: comment.loc, message: 'Code carries no comments.' });
        }
        const isTemplate = context.filename.endsWith('.vue');
        const hasTemplateComment = isTemplate && sourceCode.getText().includes('<!--');
        if (hasTemplateComment) {
          context.report({ node, message: 'Templates carry no comments.' });
        }
      },
    };
  },
};

const HTTP_ONLY_IN_SHARED = {
  name: 'axios',
  message: 'Only src/shared/http.ts talks HTTP; features call it through their api.ts.',
};
const VALIDATION_ONLY_AT_THE_BOUNDARY = {
  name: 'zod',
  message: 'Responses are validated only in a feature api.ts.',
};
const GLOBAL_STATE_ONLY = {
  name: 'pinia',
  message: 'Pinia holds only global state: the session and the selected household.',
};
const FEATURE_API_IS_PRIVATE = {
  group: ['@/features/*/api', '../*/api', '../../features/*/api'],
  message: 'A feature api.ts is private; use the feature composables.',
};
const HTTP_CLIENT_IS_FOR_APIS = {
  group: ['@/shared/http'],
  message: 'Only a feature api.ts uses the HTTP client.',
};

function restrictImports(paths, patterns) {
  return { 'no-restricted-imports': ['error', { paths, patterns }] };
}

export default defineConfigWithVueTs(
  { ignores: ['dist/**', '.quasar/**', 'node_modules/**'] },
  pluginQuasar.configs.recommended(),
  js.configs.recommended,
  pluginVue.configs['flat/recommended'],
  vueTsConfigs.strictTypeChecked,
  {
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: { ...globals.browser, ...globals.node },
    },
    plugins: { local: { rules: { 'no-comments': noComments } } },
    rules: {
      'local/no-comments': 'error',
      'vue/v-slot-style': ['error', 'shorthand'],
      'vue/max-attributes-per-line': 'off',
      'vue/singleline-html-element-content-newline': 'off',
      'vue/html-self-closing': 'off',
      '@typescript-eslint/consistent-type-imports': ['error', { prefer: 'type-imports' }],
      '@typescript-eslint/restrict-template-expressions': ['error', { allowNumber: true }],
      'no-debugger': 'error',
      'no-console': 'error',
      ...restrictImports(
        [HTTP_ONLY_IN_SHARED, VALIDATION_ONLY_AT_THE_BOUNDARY, GLOBAL_STATE_ONLY],
        [FEATURE_API_IS_PRIVATE, HTTP_CLIENT_IS_FOR_APIS],
      ),
    },
  },
  {
    files: ['src/shared/http.ts', 'src/shared/apiError.ts'],
    rules: restrictImports([GLOBAL_STATE_ONLY], []),
  },
  {
    files: ['src/features/*/api.ts'],
    rules: restrictImports([HTTP_ONLY_IN_SHARED, GLOBAL_STATE_ONLY], [FEATURE_API_IS_PRIVATE]),
  },
  {
    files: [
      'src/stores/index.ts',
      'src/features/accounts/store.ts',
      'src/features/households/store.ts',
    ],
    rules: restrictImports(
      [HTTP_ONLY_IN_SHARED, VALIDATION_ONLY_AT_THE_BOUNDARY],
      [FEATURE_API_IS_PRIVATE, HTTP_CLIENT_IS_FOR_APIS],
    ),
  },
  {
    files: ['src/features/*/components/**/*.vue'],
    rules: restrictImports(
      [HTTP_ONLY_IN_SHARED, VALIDATION_ONLY_AT_THE_BOUNDARY, GLOBAL_STATE_ONLY],
      [
        { ...FEATURE_API_IS_PRIVATE, group: [...FEATURE_API_IS_PRIVATE.group, '../api'] },
        HTTP_CLIENT_IS_FOR_APIS,
      ],
    ),
  },
  {
    files: ['src/**/*.test.ts'],
    rules: restrictImports([], []),
  },
  prettierSkipFormatting,
);
