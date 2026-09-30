const COMBINING_MARKS = /\p{M}/gu;
const WHITESPACE = /\s+/u;

export function normalizeSearchText(text: string): string {
  const decomposed = text.normalize('NFD');
  const unmarked = decomposed.replace(COMBINING_MARKS, '');
  const lowered = unmarked.toLowerCase();
  return lowered.replaceAll('ł', 'l');
}

function toSearchTerms(query: string): string[] {
  const normalized = normalizeSearchText(query);
  const terms = normalized.split(WHITESPACE);
  return terms.filter((term) => term !== '');
}

export function matchesSearch(query: string, texts: readonly string[]): boolean {
  const terms = toSearchTerms(query);
  const searchable = texts.map((text) => normalizeSearchText(text));
  return terms.every((term) => searchable.some((text) => text.includes(term)));
}
