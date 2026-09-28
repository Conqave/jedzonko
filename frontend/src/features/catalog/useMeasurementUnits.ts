import { onMounted, ref } from 'vue';
import { useApiAction } from '@/shared/useApiAction';
import { fetchMeasurementUnits } from './api';
import { CATALOG_ERROR_MESSAGES } from './errors';
import type { MeasurementUnit } from './model';

export function useMeasurementUnits() {
  const units = ref<MeasurementUnit[]>([]);
  const { run } = useApiAction(CATALOG_ERROR_MESSAGES);

  function findUnitName(code: string): string {
    const unit = units.value.find((candidate) => candidate.code === code);
    return unit === undefined ? code : unit.name;
  }

  onMounted(() => {
    void run(async () => {
      units.value = await fetchMeasurementUnits();
    });
  });

  return { units, findUnitName };
}
