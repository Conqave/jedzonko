import { defineBoot } from '#q-app';
import { Notify } from 'quasar';

const UNEXPECTED_ERROR_MESSAGE = 'Wystąpił nieoczekiwany błąd. Odśwież stronę.';

export default defineBoot(({ app }) => {
  window.addEventListener('vite:preloadError', () => {
    window.location.reload();
  });
  app.config.errorHandler = (error: unknown) => {
    Notify.create({ type: 'negative', message: UNEXPECTED_ERROR_MESSAGE });
    reportError(error);
  };
});
