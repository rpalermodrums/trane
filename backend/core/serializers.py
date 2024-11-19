from rest_framework import serializers
from .models import Entry, Note, Document, Tag
from django.contrib.auth.models import User

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
