from catalog.application.ports.product_repository import ProductRepository
from catalog.domain.product import ProductListing
from shared.household_membership import HouseholdMembershipReader, require_membership
from shared.text import normalize_text


class ListHouseholdProducts:
    def __init__(self, products: ProductRepository, memberships: HouseholdMembershipReader) -> None:
        self._products = products
        self._memberships = memberships

    def execute(self, user_id: int, household_id: int, search: str | None) -> list[ProductListing]:
        require_membership(self._memberships, user_id, household_id)
        normalized_search = None if search is None else normalize_text(search) or None
        return self._products.list_listings(household_id, normalized_search)
