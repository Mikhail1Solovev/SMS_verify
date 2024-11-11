import phonenumbers
from rest_framework import serializers

from .models import User


class PhoneNumberSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)

    def validate_phone_number(self, value):
        try:
            # Парсим номер телефона
            parsed_number = phonenumbers.parse(value, None)
            # Проверяем валидность номера
            if not phonenumbers.is_valid_number(parsed_number):
                raise serializers.ValidationError("Неверный номер телефона")
        except phonenumbers.NumberParseException:
            raise serializers.ValidationError(
                "Неверный формат номера телефона")
        return phonenumbers.format_number(parsed_number,
                                          phonenumbers.PhoneNumberFormat.E164)


class VerificationCodeSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    code = serializers.CharField(max_length=4)


class InviteCodeSerializer(serializers.Serializer):
    invite_code = serializers.CharField(max_length=6)


class UserProfileSerializer(serializers.ModelSerializer):
    invited_users = serializers.SerializerMethodField()
    invited_by = serializers.CharField(source="invited_by.phone_number",
                                       read_only=True)

    class Meta:
        model = User
        fields = ["phone_number", "invite_code", "invited_by", "invited_users"]

    def get_invited_users(self, obj):
        return obj.invited_users.values_list("phone_number", flat=True)
