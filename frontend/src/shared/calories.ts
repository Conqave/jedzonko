import { formatQuantity } from './formatQuantity';

export const UNCOUNTED_REASONS = [
  'no_amount',
  'no_calories',
  'no_piece_weight',
  'no_density',
  'no_package_weight',
] as const;

export type UncountedReason = (typeof UNCOUNTED_REASONS)[number];

export const TAG_GAPS = ['no_tag', 'several_tags'] as const;

export type TagGap = (typeof TAG_GAPS)[number];

export const ITEM_UNCOUNTED_REASONS = [...TAG_GAPS, ...UNCOUNTED_REASONS] as const;

export type ItemUncountedReason = (typeof ITEM_UNCOUNTED_REASONS)[number];

export const UNCOUNTED_REASON_LABELS: Readonly<Record<ItemUncountedReason, string>> = {
  no_tag: 'brak tagu',
  several_tags: 'kilka tagów, zostaw jeden',
  no_amount: 'brak ilości',
  no_calories: 'tag bez kalorii',
  no_piece_weight: 'tag bez wagi sztuki',
  no_density: 'tag bez gęstości',
  no_package_weight: 'nieznana waga opakowania',
};

export const UNKNOWN_KCAL_TEXT = '-';

export const ESTIMATE_LABEL = 'szac.';

export const ESTIMATE_TOOLTIP = 'Szacunek z wagi sztuki, gęstości lub opakowania.';

export type ItemCalories =
  | {
      kind: 'counted';
      kcal: string;
      kcalPer100g: string | null;
      isEstimate: boolean;
    }
  | {
      kind: 'uncounted';
      reason: ItemUncountedReason;
      kcalPer100g: string | null;
    };

export interface ItemCaloriesDto {
  kcal: string | null;
  kcal_per_100g: string | null;
  is_estimate: boolean;
  uncounted_reason: ItemUncountedReason | null;
}

export interface KcalDisplay {
  text: string;
  isKnown: boolean;
  isEstimate: boolean;
  tooltip: string | null;
  caption: string | null;
}

export function toItemCalories(dto: ItemCaloriesDto): ItemCalories {
  if (dto.kcal !== null && dto.uncounted_reason === null) {
    return {
      kind: 'counted',
      kcal: dto.kcal,
      kcalPer100g: dto.kcal_per_100g,
      isEstimate: dto.is_estimate,
    };
  }
  if (dto.kcal === null && dto.uncounted_reason !== null) {
    return { kind: 'uncounted', reason: dto.uncounted_reason, kcalPer100g: dto.kcal_per_100g };
  }
  throw new Error('Calories are either counted or carry the reason they are not.');
}

export function roundKcal(kcal: string): string {
  return Math.round(Number(kcal)).toString();
}

export function describeKcalPer100g(kcalPer100g: string): string {
  return `${formatQuantity(kcalPer100g)} kcal/100 g`;
}

export function describeItemCalories(calories: ItemCalories): KcalDisplay {
  const caption = calories.kcalPer100g === null ? null : describeKcalPer100g(calories.kcalPer100g);
  if (calories.kind === 'uncounted') {
    const reason = UNCOUNTED_REASON_LABELS[calories.reason];
    return {
      text: UNKNOWN_KCAL_TEXT,
      isKnown: false,
      isEstimate: false,
      tooltip: `Nie da się policzyć: ${reason}`,
      caption,
    };
  }
  return {
    text: `${roundKcal(calories.kcal)} kcal`,
    isKnown: true,
    isEstimate: calories.isEstimate,
    tooltip: calories.isEstimate ? ESTIMATE_TOOLTIP : null,
    caption,
  };
}

export function toKcalSortKey(calories: ItemCalories): number | null {
  return calories.kind === 'counted' ? Number(calories.kcal) : null;
}
