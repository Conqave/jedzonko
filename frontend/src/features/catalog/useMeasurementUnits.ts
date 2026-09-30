import { onMounted, ref } from 'vue';
import { useApiAction } from '@/shared/useApiAction';
import { fetchMeasurementUnits } from './api';
import { describeQuantity } from './describeQuantity';
import { CATALOG_ERROR_MESSAGES } from './errors';
import type { MeasurementUnit } from './model';

export function useMeasurementUnits() {
  const units = ref<MeasurementUnit[]>([]);
  const { run } = useApiAction(CATALOG_ERROR_MESSAGES);

  function describeUnitQuantity(quantity: string, unitCode: string): string {
    const unit = units.value.find((candidate) => candidate.code === unitCode);
    const unitName = unit === undefined ? unitCode : unit.name;
    return describeQuantity(quantity, unitCode, unitName);
  }

  onMounted(() => {
    void run(async () => {
      units.value = await fetchMeasurementUnits();
    });
  });

  return { units, describeUnitQuantity };
}
