import { describe, expect, it } from 'vitest';
import { describeItemCalories, toItemCalories, toKcalSortKey, type ItemCalories } from './calories';

const COUNTED: ItemCalories = {
  kind: 'counted',
  kcal: '1819.6',
  kcalPer100g: '364.0',
  isEstimate: false,
};

describe('item calories', () => {
  it('shows counted calories rounded with the tag value as a caption', () => {
    expect(describeItemCalories(COUNTED)).toEqual({
      text: '1820 kcal',
      isKnown: true,
      isEstimate: false,
      tooltip: null,
      caption: '364 kcal/100 g',
    });
  });

  it('marks an estimate and explains it', () => {
    const display = describeItemCalories({ ...COUNTED, isEstimate: true });

    expect(display.isEstimate).toBe(true);
    expect(display.tooltip).toBe('Szacunek z wagi sztuki, gęstości lub opakowania.');
  });

  it('shows a hyphen with the reason when calories cannot be counted', () => {
    const calories: ItemCalories = {
      kind: 'uncounted',
      reason: 'no_piece_weight',
      kcalPer100g: '143.0',
    };

    expect(describeItemCalories(calories)).toEqual({
      text: '-',
      isKnown: false,
      isEstimate: false,
      tooltip: 'Nie da się policzyć: tag bez wagi sztuki',
      caption: '143 kcal/100 g',
    });
  });

  it('sorts counted calories by value and has no key for the rest', () => {
    const untagged: ItemCalories = { kind: 'uncounted', reason: 'no_tag', kcalPer100g: null };

    expect(toKcalSortKey(COUNTED)).toBe(1819.6);
    expect(toKcalSortKey(untagged)).toBeNull();
  });

  it('refuses calories that are neither counted nor explained', () => {
    const dto = { kcal: null, kcal_per_100g: null, is_estimate: false, uncounted_reason: null };

    expect(() => toItemCalories(dto)).toThrow();
  });
});
