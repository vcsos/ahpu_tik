from rest_framework import serializers
from .models import HotBoard


class HotBoardSerializer(serializers.ModelSerializer):
    formatted_hot = serializers.CharField(read_only=True)
    title = serializers.SerializerMethodField()

    class Meta:
        model = HotBoard
        fields = ['id', 'rank', 'keyword', 'formatted_hot', 'title']

    def get_title(self, obj):
        return f"{obj.rank}. {obj.keyword} ({obj.formatted_hot})"
