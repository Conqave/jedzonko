from rest_framework import serializers


class CreateHouseholdSerializer(serializers.Serializer[dict[str, str]]):
    name = serializers.CharField(max_length=120, trim_whitespace=True)


class AddHouseholdMemberSerializer(serializers.Serializer[dict[str, str]]):
    username = serializers.CharField(max_length=150, trim_whitespace=True)
