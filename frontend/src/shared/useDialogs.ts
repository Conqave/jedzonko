import { useQuasar } from 'quasar';

export interface TextPrompt {
  title: string;
  label: string;
  initial: string;
}

export function useDialogs() {
  const quasar = useQuasar();

  function promptText(prompt: TextPrompt): Promise<string | null> {
    return new Promise((resolve) => {
      quasar
        .dialog({
          title: prompt.title,
          prompt: {
            model: prompt.initial,
            label: prompt.label,
            outlined: true,
            isValid: (value: string) => value.trim() !== '',
          },
          cancel: { flat: true, label: 'Anuluj', noCaps: true },
          ok: { label: 'Zapisz', noCaps: true },
        })
        .onOk((value: string) => {
          resolve(value.trim());
        })
        .onCancel(() => {
          resolve(null);
        });
    });
  }

  function confirm(title: string, message: string): Promise<boolean> {
    return new Promise((resolve) => {
      quasar
        .dialog({
          title,
          message,
          persistent: true,
          cancel: { flat: true, label: 'Anuluj', noCaps: true },
          ok: { color: 'negative', label: 'Tak', noCaps: true },
        })
        .onOk(() => {
          resolve(true);
        })
        .onCancel(() => {
          resolve(false);
        });
    });
  }

  function notifySuccess(message: string): void {
    quasar.notify({ type: 'positive', message });
  }

  return { promptText, confirm, notifySuccess };
}
