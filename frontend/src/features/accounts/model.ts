export interface CurrentUser {
  id: number;
  username: string;
  isStaff: boolean;
  canViewPromotions: boolean;
}
