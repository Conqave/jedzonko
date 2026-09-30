import { describe, expect, it } from 'vitest';
import {
  describeTagCalories,
  describeTagDensity,
  describeTagPieceWeight,
  groupProductDecisions,
  isDensityInput,
  isKcalInput,
  isPieceWeightInput,
  toOptionalDecimalPayload,
  type ProductIngredientDecision,
  type ProductIngredientStatus,
} from './model';

function makeDecision(id: number, status: ProductIngredientStatus): ProductIngredientDecision {
  return {
    ingredient: { id, name: `tag ${String(id)}` },
    calories: null,
    pieceWeight: null,
    density: null,
    status,
    provenance: 'model',
    modelName: 'gpt-oss:20b',
    proposedAt: new Date('2026-09-30T08:00:00+02:00'),
    decidedAt: null,
  };
}

describe('catalog model', () => {
  it('keeps confirmed tags, pending proposals and rejections apart', () => {
    const tag = makeDecision(1, 'confirmed');
    const proposal = makeDecision(2, 'proposed');
    const rejection = makeDecision(3, 'rejected');

    const groups = groupProductDecisions([rejection, tag, proposal]);

    expect(groups).toEqual({ tags: [tag], proposals: [proposal], rejections: [rejection] });
  });

  it('describes calories per 100 g of a tag', () => {
    const calories = { kcalPer100g: '52.5', provenance: 'manual' as const, referenceUrl: null };

    expect(describeTagCalories(calories)).toBe('52,5 kcal/100 g');
    expect(describeTagCalories(null)).toBe('brak kcal');
  });

  it('describes the piece weight and the density of a tag', () => {
    const source = { provenance: 'reference' as const, referenceUrl: 'https://example.org' };

    expect(describeTagPieceWeight({ ...source, gramsPerPiece: '55.0' })).toBe('55 g/szt.');
    expect(describeTagPieceWeight(null)).toBe('brak wagi sztuki');
    expect(describeTagDensity({ ...source, gramsPerMl: '1.030' })).toBe('1,03 g/ml');
    expect(describeTagDensity(null)).toBe('brak gęstości');
  });

  it('accepts calories with at most one decimal place up to 900', () => {
    expect(isKcalInput('0')).toBe(true);
    expect(isKcalInput('52')).toBe(true);
    expect(isKcalInput(' 52,5 ')).toBe(true);
    expect(isKcalInput('900')).toBe(true);
    expect(isKcalInput('901')).toBe(false);
    expect(isKcalInput('52.55')).toBe(false);
    expect(isKcalInput('dużo')).toBe(false);
    expect(isKcalInput('-5')).toBe(false);
  });

  it('accepts a positive piece weight with one decimal place up to 10 kg', () => {
    expect(isPieceWeightInput('0,2')).toBe(true);
    expect(isPieceWeightInput('55')).toBe(true);
    expect(isPieceWeightInput('10000')).toBe(true);
    expect(isPieceWeightInput('0')).toBe(false);
    expect(isPieceWeightInput('10000.1')).toBe(false);
    expect(isPieceWeightInput('55.25')).toBe(false);
    expect(isPieceWeightInput('-5')).toBe(false);
  });

  it('accepts a positive density with three decimal places up to 3 g/ml', () => {
    expect(isDensityInput('1')).toBe(true);
    expect(isDensityInput('1,03')).toBe(true);
    expect(isDensityInput('0.917')).toBe(true);
    expect(isDensityInput('3')).toBe(true);
    expect(isDensityInput('0')).toBe(false);
    expect(isDensityInput('3.001')).toBe(false);
    expect(isDensityInput('1.0305')).toBe(false);
    expect(isDensityInput('gęsto')).toBe(false);
  });

  it('turns an empty entry into clearing the value', () => {
    expect(toOptionalDecimalPayload(' ')).toBeNull();
    expect(toOptionalDecimalPayload('52,5')).toBe('52.5');
  });
});
