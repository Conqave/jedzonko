import io
from decimal import Decimal

import pytest

from catalog.domain.conversions import ConversionReference, Density, PieceWeight
from catalog.presentation.conversion_reference_file import read_conversion_references
from catalog.presentation.reference_file import InvalidReferenceFileError

HEADER = "tag,grams_per_piece,grams_per_ml,source_url\n"
EGG_URL = "https://example.org/egg"
MILK_URL = "https://example.org/milk"


def _read(text: str) -> tuple[ConversionReference, ...]:
    stream = io.StringIO(text)
    return read_conversion_references(stream)


def test_rows_become_reference_conversions_and_empty_cells_are_not_provided() -> None:
    references = _read(
        HEADER + f"jajka,55,,{EGG_URL}\n" f'mleko,,"1,03",{MILK_URL}\n' f"miód,20,1.42,{MILK_URL}\n"
    )

    assert references == (
        ConversionReference(
            tag_name="jajka",
            piece_weight=PieceWeight.from_reference(Decimal("55"), EGG_URL),
            density=None,
        ),
        ConversionReference(
            tag_name="mleko",
            piece_weight=None,
            density=Density.from_reference(Decimal("1.03"), MILK_URL),
        ),
        ConversionReference(
            tag_name="miód",
            piece_weight=PieceWeight.from_reference(Decimal("20"), MILK_URL),
            density=Density.from_reference(Decimal("1.42"), MILK_URL),
        ),
    )


@pytest.mark.parametrize(
    "text",
    [
        "tag,kcal_per_100g,source_url\njajka,143,https://example.org/egg\n",
        HEADER + "jajka,55,https://example.org/egg\n",
        HEADER + ",55,,https://example.org/egg\n",
        HEADER + "jajka,,,https://example.org/egg\n",
        HEADER + "jajka,dużo,,https://example.org/egg\n",
        HEADER + "jajka,0,,https://example.org/egg\n",
        HEADER + "jajka,55.25,,https://example.org/egg\n",
        HEADER + "mleko,,4,https://example.org/milk\n",
        HEADER + "mleko,,1.0305,https://example.org/milk\n",
        HEADER + "jajka,55,,\n",
        HEADER + "jajka,55,,ftp://example.org/egg\n",
        "",
    ],
)
def test_a_malformed_conversion_file_is_refused_whole(text: str) -> None:
    with pytest.raises(InvalidReferenceFileError):
        _read(text)
