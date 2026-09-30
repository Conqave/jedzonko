import { computed, type WritableComputedRef } from 'vue';
import { useRoute, useRouter, type LocationQuery } from 'vue-router';

const FLAG_ON = '1';

export function readQueryText(query: LocationQuery, name: string): string {
  const value = query[name];
  const first = Array.isArray(value) ? value[0] : value;
  return typeof first === 'string' ? first : '';
}

export function readQueryChoice<Choice extends string>(
  query: LocationQuery,
  name: string,
  choices: readonly Choice[],
  fallback: Choice,
): Choice {
  const text = readQueryText(query, name);
  const choice = choices.find((candidate) => candidate === text);
  return choice ?? fallback;
}

export function readQueryFlag(query: LocationQuery, name: string): boolean {
  return readQueryText(query, name) === FLAG_ON;
}

export function withQueryValue(
  query: LocationQuery,
  name: string,
  value: string | null,
): LocationQuery {
  const kept = Object.entries(query).filter(([key]) => key !== name);
  const others: LocationQuery = Object.fromEntries(kept);
  return value === null ? others : { ...others, [name]: value };
}

export function useRouteQuery() {
  const route = useRoute();
  const router = useRouter();

  function setValue(name: string, value: string | null): void {
    const query = withQueryValue(route.query, name, value);
    void router.replace({ query });
  }

  function textParam(name: string): WritableComputedRef<string> {
    return computed({
      get: () => readQueryText(route.query, name),
      set: (text) => {
        setValue(name, text === '' ? null : text);
      },
    });
  }

  function choiceParam<Choice extends string>(
    name: string,
    choices: readonly Choice[],
    fallback: Choice,
  ): WritableComputedRef<Choice> {
    return computed({
      get: () => readQueryChoice(route.query, name, choices, fallback),
      set: (choice) => {
        setValue(name, choice === fallback ? null : choice);
      },
    });
  }

  function flagParam(name: string): WritableComputedRef<boolean> {
    return computed({
      get: () => readQueryFlag(route.query, name),
      set: (isOn) => {
        setValue(name, isOn ? FLAG_ON : null);
      },
    });
  }

  return { textParam, choiceParam, flagParam };
}

export function useListQuery<Sort extends string>(sorts: readonly Sort[], defaultSort: Sort) {
  const query = useRouteQuery();
  const search = query.textParam('q');
  const sort = query.choiceParam('sort', sorts, defaultSort);
  const isReversed = query.flagParam('rev');
  return { query, search, sort, isReversed };
}
