from rest_framework import serializers


class CreateHouseholdSerializer(serializers.Serializer[dict[str, str]]):
    name = serializers.CharField(max_length=120, trim_whitespace=True)


class RenameHouseholdSerializer(serializers.Serializer[dict[str, str]]):
    name = serializers.CharField(max_length=120, trim_whitespace=True)


class AddHouseholdMemberSerializer(serializers.Serializer[dict[str, str]]):
    username = serializers.CharField(max_length=150, trim_whitespace=True)


class HouseholdSerializer(serializers.Serializer[object]):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    member_count = serializers.IntegerField(read_only=True)


class DeletedHouseholdSerializer(HouseholdSerializer):
    deleted_at = serializers.DateTimeField(read_only=True)
    purge_after = serializers.DateTimeField(read_only=True)


class HouseholdMemberSerializer(serializers.Serializer[object]):
    user_id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
