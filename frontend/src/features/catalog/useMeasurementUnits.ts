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
    return describeQuantity(quantity, unitCode, units.value);
  }

  onMounted(() => {
    void run(async () => {
      units.value = await fetchMeasurementUnits();
    });
  });

  return { units, describeUnitQuantity };
}
