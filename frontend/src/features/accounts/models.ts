export interface CurrentUser {
  id: number;
  username: string;
  is_staff: boolean;
  can_view_promotions: boolean;
}

export interface ApiError {
  code: string;
  detail: string;
}
