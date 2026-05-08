from rest_framework import serializers

class ChatMessageSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=["user", "assistant", "system"])
    content = serializers.CharField()

class ChatRequestSerializer(serializers.Serializer):
    messages = ChatMessageSerializer(many=True)
