import { formatQuantity } from '@/shared/formatQuantity';

interface UnitForms {
  one: string;
  few: string;
  many: string;
  other: string;
}

const UNIT_FORMS: Readonly<Record<string, UnitForms>> = {
  g: { one: 'gram', few: 'gramy', many: 'gramów', other: 'grama' },
  kg: { one: 'kilogram', few: 'kilogramy', many: 'kilogramów', other: 'kilograma' },
  ml: { one: 'mililitr', few: 'mililitry', many: 'mililitrów', other: 'mililitra' },
  l: { one: 'litr', few: 'litry', many: 'litrów', other: 'litra' },
  szt: { one: 'sztuka', few: 'sztuki', many: 'sztuk', other: 'sztuki' },
};

const POLISH_PLURAL_RULES = new Intl.PluralRules('pl-PL');

export function describeQuantity(quantity: string, unitCode: string, unitName: string): string {
  const amount = formatQuantity(quantity);
  const forms = UNIT_FORMS[unitCode];
  if (forms === undefined) {
    return `${amount} ${unitName}`;
  }
  const category = POLISH_PLURAL_RULES.select(Number(amount));
  const unit =
    category === 'one' || category === 'few' || category === 'many' ? forms[category] : forms.other;
  return `${amount} ${unit}`;
}
