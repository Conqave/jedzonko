from decimal import Decimal

from rest_framework import serializers

from catalog.domain.product import ProductPackage


class PackageSerializer(serializers.Serializer[ProductPackage]):
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=Decimal("0.001"))
    unit_code = serializers.CharField(max_length=16)


class ProductQuerySerializer(serializers.Serializer[dict[str, object]]):
    household_id = serializers.IntegerField(min_value=1)
    search = serializers.CharField(max_length=120, required=False, trim_whitespace=True)


class CreateProductSerializer(serializers.Serializer[dict[str, object]]):
    household_id = serializers.IntegerField(min_value=1)
    name = serializers.CharField(max_length=120, trim_whitespace=True)
    default_unit_code = serializers.CharField(max_length=16)
    is_food = serializers.BooleanField(default=True)
    package = PackageSerializer(required=False, allow_null=True, default=None)


class UpdateProductSerializer(serializers.Serializer[dict[str, object]]):
    name = serializers.CharField(max_length=120, trim_whitespace=True)
    package = PackageSerializer(allow_null=True)


class ProductSerializer(serializers.Serializer[object]):
    id = serializers.IntegerField(read_only=True)
    household_id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    default_unit_code = serializers.CharField(read_only=True)
    is_food = serializers.BooleanField(read_only=True)
    package = PackageSerializer(read_only=True, allow_null=True)


class IngredientSerializer(serializers.Serializer[object]):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)


class ProductTagSerializer(serializers.Serializer[object]):
    ingredient_id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)


class ProductListingSerializer(serializers.Serializer[object]):
    product = ProductSerializer(read_only=True)
    tags = ProductTagSerializer(many=True, read_only=True)
    open_proposal_count = serializers.IntegerField(read_only=True)


class ProductIngredientLinkSerializer(serializers.Serializer[object]):
    ingredient = IngredientSerializer(read_only=True)
    status = serializers.CharField(source="link.status", read_only=True)
    provenance = serializers.CharField(source="link.source", read_only=True)
    model_name = serializers.CharField(source="link.model_name", read_only=True, allow_null=True)
    proposed_at = serializers.DateTimeField(source="link.proposed_at", read_only=True)
    decided_at = serializers.DateTimeField(source="link.decided_at", read_only=True)


class IngredientQuerySerializer(serializers.Serializer[dict[str, str]]):
    search = serializers.CharField(max_length=120, trim_whitespace=True)


class MeasurementUnitSerializer(serializers.Serializer[object]):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    dimension = serializers.CharField(read_only=True)
    factor_to_base = serializers.DecimalField(max_digits=12, decimal_places=3, read_only=True)


def to_package(data: object) -> ProductPackage | None:
    if data is None:
        return None
    if not isinstance(data, dict):
        raise TypeError("package must be validated data")
    return ProductPackage(quantity=data["quantity"], unit_code=str(data["unit_code"]))
