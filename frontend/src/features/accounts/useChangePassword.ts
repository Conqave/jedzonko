import { useApiAction } from '@/shared/useApiAction';
import { changePassword } from './api';
import { ACCOUNT_ERROR_MESSAGES } from './errors';

export function useChangePassword() {
  const { busy, run } = useApiAction(ACCOUNT_ERROR_MESSAGES);

  function change(currentPassword: string, newPassword: string): Promise<boolean> {
    return run(() => changePassword(currentPassword, newPassword));
  }

  return { busy, change };
}
