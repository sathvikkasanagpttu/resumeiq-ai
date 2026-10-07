import '@testing-library/jest-dom';
import { beforeEach } from 'vitest';

// Polyfill or safely clear storage in test environment
beforeEach(() => {
  try {
    if (typeof sessionStorage !== 'undefined' && typeof sessionStorage.clear === 'function') {
      sessionStorage.clear();
    }
  } catch (_) {}

  try {
    if (typeof localStorage !== 'undefined' && typeof localStorage.clear === 'function') {
      localStorage.clear();
    }
  } catch (_) {}
});
