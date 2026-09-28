import type { ErrorMessages } from '@/shared/apiError';

export const HOUSEHOLD_ERROR_MESSAGES: ErrorMessages = {
  household_not_found: 'Nie znaleziono gospodarstwa domowego.',
  user_not_found: 'Nie znaleziono użytkownika o podanej nazwie.',
  member_not_found: 'Ta osoba nie należy do gospodarstwa domowego.',
  last_member_cannot_leave: 'Nie można usunąć ostatniego członka gospodarstwa domowego.',
  recovery_window_expired: 'Minął czas na przywrócenie tego gospodarstwa domowego.',
};
