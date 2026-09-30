import { describe, expect, it } from 'vitest';
import { describeTagCalories, isKcalInput, toKcalPayload } from './model';

describe('catalog model', () => {
  it('describes calories per 100 g of a tag', () => {
    const calories = { kcalPer100g: '52.5', provenance: 'manual' as const, referenceUrl: null };

    expect(describeTagCalories(calories)).toBe('52,5 kcal/100 g');
    expect(describeTagCalories(null)).toBe('brak kcal');
  });

  it('accepts calories with at most one decimal place', () => {
    expect(isKcalInput('52')).toBe(true);
    expect(isKcalInput(' 52,5 ')).toBe(true);
    expect(isKcalInput('52.55')).toBe(false);
    expect(isKcalInput('dużo')).toBe(false);
    expect(isKcalInput('-5')).toBe(false);
  });

  it('turns an empty entry into clearing the calories', () => {
    expect(toKcalPayload(' ')).toBeNull();
    expect(toKcalPayload('52,5')).toBe('52.5');
  });
});
