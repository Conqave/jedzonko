import { divideByThousand, toThousandths } from '@/shared/decimal';
import { formatQuantity } from '@/shared/formatQuantity';
import { isBaseUnit, type MeasurementUnit } from './model';

interface UnitForms {
  one: string;
  few: string;
  many: string;
  other: string;
}

interface UnitQuantity {
  quantity: string;
  unit: MeasurementUnit;
}

const UNIT_FORMS: Readonly<Record<string, UnitForms>> = {
  g: { one: 'gram', few: 'gramy', many: 'gramów', other: 'grama' },
  kg: { one: 'kilogram', few: 'kilogramy', many: 'kilogramów', other: 'kilograma' },
  ml: { one: 'mililitr', few: 'mililitry', many: 'mililitrów', other: 'mililitra' },
  l: { one: 'litr', few: 'litry', many: 'litrów', other: 'litra' },
  szt: { one: 'sztuka', few: 'sztuki', many: 'sztuk', other: 'sztuki' },
};

const THOUSAND_IN_THOUSANDTHS = 1000000n;

const POLISH_PLURAL_RULES = new Intl.PluralRules('pl-PL');

function findThousandfoldUnit(
  unit: MeasurementUnit,
  units: readonly MeasurementUnit[],
): MeasurementUnit | undefined {
  return units.find(
    (candidate) =>
      candidate.dimension === unit.dimension &&
      toThousandths(candidate.factorToBase) === THOUSAND_IN_THOUSANDTHS,
  );
}

function toReadableQuantity(
  quantity: string,
  unit: MeasurementUnit,
  units: readonly MeasurementUnit[],
): UnitQuantity {
  const original: UnitQuantity = { quantity, unit };
  if (!isBaseUnit(unit) || toThousandths(quantity) < THOUSAND_IN_THOUSANDTHS) {
    return original;
  }
  const thousandfoldUnit = findThousandfoldUnit(unit, units);
  if (thousandfoldUnit === undefined) {
    return original;
  }
  return { quantity: divideByThousand(quantity), unit: thousandfoldUnit };
}

function nameUnit(quantity: string, unit: MeasurementUnit): string {
  const forms = UNIT_FORMS[unit.code];
  if (forms === undefined) {
    return unit.name;
  }
  const category = POLISH_PLURAL_RULES.select(Number(quantity));
  return category === 'one' || category === 'few' || category === 'many'
    ? forms[category]
    : forms.other;
}

export function describeQuantity(
  quantity: string,
  unitCode: string,
  units: readonly MeasurementUnit[],
): string {
  const unit = units.find((candidate) => candidate.code === unitCode);
  if (unit === undefined) {
    return `${formatQuantity(quantity)} ${unitCode}`;
  }
  const readable = toReadableQuantity(quantity, unit, units);
  const amount = formatQuantity(readable.quantity);
  const unitName = nameUnit(readable.quantity, readable.unit);
  return `${amount} ${unitName}`;
}
