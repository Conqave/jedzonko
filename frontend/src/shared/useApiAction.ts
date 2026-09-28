import { useQuasar } from 'quasar';
import { ref } from 'vue';
import { describeApiError, type ErrorMessages } from './apiError';

export function useApiAction(messages: ErrorMessages) {
  const quasar = useQuasar();
  const busy = ref(false);

  async function run(action: () => Promise<void>): Promise<boolean> {
    busy.value = true;
    try {
      await action();
      return true;
    } catch (error: unknown) {
      const message = describeApiError(error, messages);
      quasar.notify({ type: 'negative', message });
      return false;
    } finally {
      busy.value = false;
    }
  }

  return { busy, run };
}
