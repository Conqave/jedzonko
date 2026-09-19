from rest_framework import serializers


class CreateHouseholdSerializer(serializers.Serializer[dict[str, str]]):
    name = serializers.CharField(max_length=120, trim_whitespace=True)


class AddHouseholdMemberSerializer(serializers.Serializer[dict[str, str]]):
    username = serializers.CharField(max_length=150, trim_whitespace=True)


class ProductQuerySerializer(serializers.Serializer[dict[str, object]]):
    household_id = serializers.IntegerField(min_value=1)
    search = serializers.CharField(max_length=120, required=False, trim_whitespace=True)


class CreateProductSerializer(serializers.Serializer[dict[str, object]]):
    household_id = serializers.IntegerField(min_value=1)
    name = serializers.CharField(max_length=120, trim_whitespace=True)
    default_unit_code = serializers.CharField(max_length=16, trim_whitespace=True)
    is_food = serializers.BooleanField(required=False, default=True)


class RenameHouseholdSerializer(serializers.Serializer[dict[str, str]]):
    name = serializers.CharField(max_length=120, trim_whitespace=True)
