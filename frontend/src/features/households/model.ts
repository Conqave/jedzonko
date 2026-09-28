export interface Household {
  id: number;
  name: string;
  memberCount: number;
}

export interface DeletedHousehold extends Household {
  deletedAt: Date;
  purgeAfter: Date;
}

export interface HouseholdMember {
  userId: number;
  username: string;
}
