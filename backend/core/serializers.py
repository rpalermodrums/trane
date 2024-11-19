from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

from core.models import Entry, Note, Document, Tag

User = get_user_model()

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'

class NoteSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Note
        fields = '__all__'

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'

class EntrySerializer(serializers.ModelSerializer):
    notes = NoteSerializer(many=True, required=False)
    documents = DocumentSerializer(many=True, required=False)

    class Meta:
        model = Entry
        fields = '__all__'
        read_only_fields = ('user', 'created_by', 'updated_by')

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')
        extra_kwargs = {
            'password': {'write_only': True}
        }
