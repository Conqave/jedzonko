from rest_framework import serializers


class ChangePasswordSerializer(serializers.Serializer[dict[str, str]]):
    current_password = serializers.CharField(max_length=128, trim_whitespace=False)
    new_password = serializers.CharField(max_length=128, min_length=8, trim_whitespace=False)


class LoginSerializer(serializers.Serializer[dict[str, str]]):
    username = serializers.CharField(max_length=150, trim_whitespace=True)
    password = serializers.CharField(max_length=128, trim_whitespace=False)


class AuthenticatedUserSerializer(serializers.Serializer[object]):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    is_staff = serializers.BooleanField(read_only=True)
    can_view_promotions = serializers.BooleanField(read_only=True)
