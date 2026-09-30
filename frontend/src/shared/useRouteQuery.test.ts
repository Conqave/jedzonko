import { flushPromises, mount } from '@vue/test-utils';
import { defineComponent, h } from 'vue';
import { describe, expect, it } from 'vitest';
import { createMemoryHistory, createRouter } from 'vue-router';
import {
  readQueryChoice,
  readQueryFlag,
  readQueryText,
  useRouteQuery,
  withQueryValue,
} from './useRouteQuery';

const STATUSES = ['all', 'pending', 'purchased'] as const;

describe('route query parsing', () => {
  it('reads the first text value and nothing for a missing name', () => {
    expect(readQueryText({ q: 'mleko' }, 'q')).toBe('mleko');
    expect(readQueryText({ q: ['ser', 'chleb'] }, 'q')).toBe('ser');
    expect(readQueryText({ q: null }, 'q')).toBe('');
    expect(readQueryText({}, 'q')).toBe('');
  });

  it('reads a known choice and falls back for an unknown one', () => {
    expect(readQueryChoice({ status: 'pending' }, 'status', STATUSES, 'all')).toBe('pending');
    expect(readQueryChoice({ status: 'lost' }, 'status', STATUSES, 'all')).toBe('all');
    expect(readQueryChoice({}, 'status', STATUSES, 'all')).toBe('all');
  });

  it('reads a flag only when it is switched on', () => {
    expect(readQueryFlag({ low: '1' }, 'low')).toBe(true);
    expect(readQueryFlag({ low: 'yes' }, 'low')).toBe(false);
    expect(readQueryFlag({}, 'low')).toBe(false);
  });

  it('sets or drops one value and keeps the others', () => {
    expect(withQueryValue({ q: 'ser', tab: 'all' }, 'q', 'chleb')).toEqual({
      q: 'chleb',
      tab: 'all',
    });
    expect(withQueryValue({ q: 'ser', tab: 'all' }, 'q', null)).toEqual({ tab: 'all' });
  });
});

describe('route query state', () => {
  async function mountWithQuery(path: string) {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/list', name: 'list', component: { render: () => null } }],
    });
    await router.push(path);
    const state: { params: ReturnType<typeof bindParams> | null } = { params: null };
    function bindParams() {
      const query = useRouteQuery();
      return {
        search: query.textParam('q'),
        status: query.choiceParam('status', STATUSES, 'all'),
        isLow: query.flagParam('low'),
      };
    }
    const Probe = defineComponent({
      setup() {
        state.params = bindParams();
        return () => h('div');
      },
    });
    mount(Probe, { global: { plugins: [router] } });
    if (state.params === null) {
      throw new Error('The probe did not bind its parameters.');
    }
    return { router, params: state.params };
  }

  it('reads the filters from the current URL', async () => {
    const { params } = await mountWithQuery('/list?q=mleko&status=purchased&low=1');

    expect(params.search.value).toBe('mleko');
    expect(params.status.value).toBe('purchased');
    expect(params.isLow.value).toBe(true);
  });

  it('writes filters to the URL and drops the default values', async () => {
    const { router, params } = await mountWithQuery('/list?status=pending');

    params.search.value = 'ser';
    await flushPromises();
    params.status.value = 'all';
    await flushPromises();
    params.isLow.value = true;
    await flushPromises();

    expect(router.currentRoute.value.query).toEqual({ q: 'ser', low: '1' });
  });
});
