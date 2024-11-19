from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from core.tasks import process_audio
from transcribe.tasks import example_task
from .models import Entry, Note, Document, Tag
from .serializers import EntrySerializer, NoteSerializer, DocumentSerializer, TagSerializer

class EntryViewSet(viewsets.ModelViewSet):
    queryset = Entry.objects.all()
    serializer_class = EntrySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        entry = serializer.save(user=self.request.user, created_by=self.request.user, updated_by=self.request.user)
        process_audio.delay(entry.id)

    @action(detail=False, methods=['post'])
    def process_cli(self, request):
        """Handle CLI processing requests"""
        if 'audio_file' not in request.FILES:
            return Response(
                {'error': 'Audio file is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        audio_file = request.FILES['audio_file']
        model = request.data.get('model', 'htdemucs')
        instruments = request.data.get('instruments', [])

        # Create entry and trigger processing
        entry = Entry.objects.create(
            user=request.user,
            created_by=request.user,  # Add this
            updated_by=request.user,  # Add this
            audio_file=audio_file,
            processing_status='pending',
            model_version=model,
            processing_options={'instruments': instruments}
        )
        
        process_audio.delay(entry.id)
        
        return Response({
            'task_id': entry.id,
            'status': 'pending'
        })

    @action(detail=True, methods=['get'])
    def task_status(self, request, pk=None):
        """Get task status"""
        try:
            entry = self.get_queryset().get(pk=pk)
            return Response({
                'task_id': entry.id,
                'status': entry.processing_status
            })
        except Entry.DoesNotExist:
            return Response(
                {'error': 'Task not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class NoteViewSet(viewsets.ModelViewSet):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)


def example_task(request):
    example_task.delay()
    return HttpResponse("Task triggered")