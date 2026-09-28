import { AxiosError, AxiosHeaders, type AxiosResponse } from 'axios';
import { describe, expect, it } from 'vitest';
import { describeApiError, findErrorCode } from './apiError';

const MESSAGES = { user_not_found: 'Nie ma takiej osoby.' };

function makeResponseError(status: number, data: unknown): AxiosError {
  const config = { headers: new AxiosHeaders() };
  const response: AxiosResponse = { status, statusText: '', headers: {}, config, data };
  return new AxiosError('Request failed', 'ERR_BAD_RESPONSE', config, null, response);
}

describe('describeApiError', () => {
  it('shows the message of a known error code', () => {
    const error = makeResponseError(404, { code: 'user_not_found', detail: 'User not found.' });

    expect(describeApiError(error, MESSAGES)).toBe('Nie ma takiej osoby.');
  });

  it('shows a common message for membership errors', () => {
    const error = makeResponseError(403, { code: 'not_a_household_member', detail: 'No.' });

    expect(describeApiError(error, MESSAGES)).toBe('Nie należysz do tego gospodarstwa domowego.');
  });

  it('reports an unreachable server when no response arrives', () => {
    const error = new AxiosError('Network Error', 'ERR_NETWORK');

    expect(describeApiError(error, MESSAGES)).toContain('niedostępny');
  });

  it('reports an unreachable server on a server failure', () => {
    const error = makeResponseError(502, '<html></html>');

    expect(describeApiError(error, MESSAGES)).toContain('niedostępny');
  });

  it('rethrows an error code nobody expects', () => {
    const error = makeResponseError(409, { code: 'surprise', detail: 'Surprise.' });

    expect(() => describeApiError(error, MESSAGES)).toThrow(error);
  });

  it('rethrows programming errors', () => {
    const error = new TypeError('undefined is not a function');

    expect(() => describeApiError(error, MESSAGES)).toThrow(error);
  });
});

describe('findErrorCode', () => {
  it('ignores a body that breaks the error contract', () => {
    const error = makeResponseError(400, { detail: 'no code' });

    expect(findErrorCode(error)).toBeNull();
  });
});
