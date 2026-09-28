class HouseholdNotFoundError(Exception):
    pass


class NotAHouseholdMemberError(Exception):
    pass


class RecoveryWindowExpiredError(Exception):
    pass


class MemberNotFoundError(Exception):
    pass


class LastMemberCannotLeaveError(Exception):
    pass


class ProductNotFoundError(Exception):
    pass


class DuplicateProductError(Exception):
    pass


class MeasurementUnitNotFoundError(Exception):
    pass


class AliasProposalNotFoundError(Exception):
    pass


class AliasProposalNotPendingError(Exception):
    pass
