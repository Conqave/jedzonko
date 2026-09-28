const FALLBACK_EMOJI = '📦';

const EMOJI_BY_KEYWORD: ReadonlyArray<readonly [string, string]> = [
  ['awokado', '🥑'],
  ['jajko', '🥚'],
  ['jajka', '🥚'],
  ['jaja', '🥚'],
  ['mleko', '🥛'],
  ['maslanka', '🥛'],
  ['skyr', '🥛'],
  ['smietanka', '🥛'],
  ['smietana', '🥛'],
  ['kefir', '🥛'],
  ['maslo', '🧈'],
  ['ser', '🧀'],
  ['serek', '🧀'],
  ['twarog', '🧀'],
  ['burrata', '🧀'],
  ['maasdammer', '🧀'],
  ['chleb', '🍞'],
  ['pumpernikiel', '🍞'],
  ['bulka', '🥖'],
  ['makaron', '🍝'],
  ['swiderki', '🍝'],
  ['ryz', '🍚'],
  ['kasza', '🍚'],
  ['maka', '🌾'],
  ['cukier', '🍬'],
  ['zelki', '🍬'],
  ['cukierki', '🍬'],
  ['cebula', '🧅'],
  ['dymka', '🧅'],
  ['czosnek', '🧄'],
  ['papryka', '🫑'],
  ['pomidor', '🍅'],
  ['pomidory', '🍅'],
  ['passata', '🥫'],
  ['przecier', '🥫'],
  ['koncentrat', '🥫'],
  ['fasola', '🫘'],
  ['soczewica', '🫘'],
  ['ziemniaki', '🥔'],
  ['ziemniak', '🥔'],
  ['batat', '🍠'],
  ['bataty', '🍠'],
  ['marchew', '🥕'],
  ['marchewka', '🥕'],
  ['pietruszka', '🌿'],
  ['koperek', '🌿'],
  ['mieta', '🌿'],
  ['pesto', '🌿'],
  ['brukselka', '🥬'],
  ['salata', '🥬'],
  ['kapusta', '🥬'],
  ['cukinia', '🥒'],
  ['ogorek', '🥒'],
  ['pieczarki', '🍄'],
  ['kurki', '🍄'],
  ['grzyby', '🍄'],
  ['slonecznik', '🌻'],
  ['dzem', '🍯'],
  ['miod', '🍯'],
  ['herbata', '🍵'],
  ['kawa', '☕'],
  ['napoj', '🥤'],
  ['woda', '💧'],
  ['sok', '🧃'],
  ['kabanosy', '🌭'],
  ['parowki', '🌭'],
  ['musztarda', '🌭'],
  ['prosciutto', '🥓'],
  ['boczek', '🥓'],
  ['szynka', '🍖'],
  ['kurczak', '🍗'],
  ['ryba', '🐟'],
  ['losos', '🐟'],
  ['oliwa', '🫒'],
  ['olej', '🫒'],
  ['sol', '🧂'],
  ['pieprz', '🧂'],
  ['mydlo', '🧼'],
  ['plyn', '🧴'],
  ['pasta', '🪥'],
  ['maszynka', '🪒'],
  ['folia', '🧻'],
  ['papier', '🧻'],
];

function normalize(value: string): string {
  return value.toLowerCase().replace(/ł/g, 'l').normalize('NFKD').replace(/[̀-ͯ]/g, '');
}

export function productEmoji(productName: string): string {
  const words = new Set(
    normalize(productName)
      .split(/[^a-z0-9]+/)
      .filter(Boolean),
  );
  for (const [keyword, emoji] of EMOJI_BY_KEYWORD) {
    if (words.has(keyword)) {
      return emoji;
    }
  }
  return FALLBACK_EMOJI;
}
