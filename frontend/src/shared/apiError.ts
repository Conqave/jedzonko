import axios from 'axios';
import { z } from 'zod';

export type ErrorMessages = Readonly<Record<string, string>>;

const errorBodySchema = z.object({ code: z.string(), detail: z.string() });

const COMMON_MESSAGES: ErrorMessages = {
  not_authenticated: 'Sesja wygasła. Zaloguj się ponownie.',
  not_a_household_member: 'Nie należysz do tego gospodarstwa domowego.',
  permission_denied: 'Brak uprawnień do tej operacji.',
  not_found: 'Nie znaleziono zasobu.',
  invalid: 'Nieprawidłowe dane.',
};

const UNREACHABLE_SERVER_MESSAGE = 'Serwer jest chwilowo niedostępny. Spróbuj ponownie.';
const FIRST_SERVER_ERROR_STATUS = 500;

export function findErrorCode(error: unknown): string | null {
  if (!axios.isAxiosError(error) || error.response === undefined) {
    return null;
  }
  const body = errorBodySchema.safeParse(error.response.data);
  return body.success ? body.data.code : null;
}

function isServerUnreachable(error: unknown): boolean {
  if (!axios.isAxiosError(error)) {
    return false;
  }
  if (error.response === undefined) {
    return true;
  }
  return error.response.status >= FIRST_SERVER_ERROR_STATUS;
}

export function describeApiError(error: unknown, messages: ErrorMessages): string {
  const code = findErrorCode(error);
  const message = code === null ? undefined : (messages[code] ?? COMMON_MESSAGES[code]);
  if (message !== undefined) {
    return message;
  }
  if (isServerUnreachable(error)) {
    return UNREACHABLE_SERVER_MESSAGE;
  }
  throw error;
}
