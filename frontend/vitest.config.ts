// vitest.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    // Use jsdom to provide a DOM environment for React hooks testing
    environment: 'jsdom',
    globals: true,
    // Clear mocks between tests
    clearMocks: true,
    // Setup a minimal global environment if needed
    // setupFiles: [],
  },
});
