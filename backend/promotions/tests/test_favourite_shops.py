import pytest

from promotions.application.errors import UnknownShopError
from promotions.application.use_cases.list_favourite_shops import ListFavouriteShops
from promotions.application.use_cases.set_favourite_shops import SetFavouriteShops
from promotions.domain.models import FavouriteShop
from promotions.tests.fakes import FakeFavouriteShopRepository, FakePromotionSource

USER_ID = 7
OTHER_USER_ID = 8


def test_set_favourite_shops_resolves_display_names_from_the_provider() -> None:
    repository = FakeFavouriteShopRepository({})

    result = SetFavouriteShops(repository, FakePromotionSource({})).execute(
        USER_ID, ("lidl", "biedronka")
    )

    assert sorted((shop.slug, shop.name) for shop in result) == [
        ("biedronka", "Biedronka"),
        ("lidl", "Lidl"),
    ]


def test_set_favourite_shops_replaces_the_previous_selection() -> None:
    repository = FakeFavouriteShopRepository({USER_ID: [FavouriteShop(name="Lidl", slug="lidl")]})
    use_case = SetFavouriteShops(repository, FakePromotionSource({}))

    use_case.execute(USER_ID, ("carrefour",))

    assert [shop.slug for shop in ListFavouriteShops(repository).execute(USER_ID)] == ["carrefour"]


def test_set_favourite_shops_accepts_an_empty_selection() -> None:
    repository = FakeFavouriteShopRepository({USER_ID: [FavouriteShop(name="Lidl", slug="lidl")]})

    result = SetFavouriteShops(repository, FakePromotionSource({})).execute(USER_ID, ())

    assert result == []
    assert ListFavouriteShops(repository).execute(USER_ID) == []


def test_set_favourite_shops_rejects_unknown_slugs() -> None:
    repository = FakeFavouriteShopRepository({})

    with pytest.raises(UnknownShopError):
        SetFavouriteShops(repository, FakePromotionSource({})).execute(USER_ID, ("biedornka",))


def test_set_favourite_shops_does_not_touch_another_user_selection() -> None:
    repository = FakeFavouriteShopRepository(
        {OTHER_USER_ID: [FavouriteShop(name="Lidl", slug="lidl")]}
    )

    SetFavouriteShops(repository, FakePromotionSource({})).execute(USER_ID, ("carrefour",))

    assert [shop.slug for shop in ListFavouriteShops(repository).execute(OTHER_USER_ID)] == ["lidl"]


def test_list_favourite_shops_is_empty_for_a_user_without_a_selection() -> None:
    repository = FakeFavouriteShopRepository({})

    assert ListFavouriteShops(repository).execute(USER_ID) == []
