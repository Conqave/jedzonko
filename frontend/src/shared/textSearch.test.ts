import { describe, expect, it } from 'vitest';
import { matchesSearch, normalizeSearchText } from './textSearch';

describe('text search', () => {
  it('folds case and Polish diacritics, including ł', () => {
    expect(normalizeSearchText('Źdźbło ŻÓŁTEJ Mąki')).toBe('zdzblo zoltej maki');
  });

  it('matches every text for a blank query', () => {
    expect(matchesSearch('', ['mleko'])).toBe(true);
    expect(matchesSearch('   ', [])).toBe(true);
  });

  it('finds a fragment regardless of diacritics on either side', () => {
    expect(matchesSearch('mak', ['Mąka pszenna'])).toBe(true);
    expect(matchesSearch('MĄKA', ['maka'])).toBe(true);
    expect(matchesSearch('zolty', ['Ser żółty'])).toBe(true);
  });

  it('needs every word of the query, each in any of the texts', () => {
    expect(matchesSearch('ser nabiał', ['Ser gouda', 'Nabiał'])).toBe(true);
    expect(matchesSearch('ser mięso', ['Ser gouda', 'Nabiał'])).toBe(false);
  });

  it('rejects texts without the query', () => {
    expect(matchesSearch('chleb', ['Mleko', 'Nabiał'])).toBe(false);
    expect(matchesSearch('chleb', [])).toBe(false);
  });
});
