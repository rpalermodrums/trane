from django.http import HttpResponse, StreamingHttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from wsgiref.util import FileWrapper
import os
import mimetypes

from core.tasks import process_audio
from transcribe.tasks import example_task
from core.models import Entry, Note, Document, Tag
from core.serializers import EntrySerializer, NoteSerializer, DocumentSerializer, TagSerializer

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

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download the processed audio file with proper headers for streaming"""
        entry = self.get_object()
        
        # Check if the file exists
        if not os.path.exists(entry.audio_file.path):
            return Response(
                {'error': 'File not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Get file info
        file_size = os.path.getsize(entry.audio_file.path)
        content_type = mimetypes.guess_type(entry.audio_file.path)[0]

        # Handle range header for streaming
        range_header = request.META.get('HTTP_RANGE', '').strip()
        range_match = range_header.replace('bytes=', '').split('-')
        range_start = int(range_match[0]) if range_match[0] else 0
        range_end = min(int(range_match[1]), file_size - 1) if range_match[1] else file_size - 1
        length = range_end - range_start + 1

        # Create response
        response = StreamingHttpResponse(
            FileWrapper(open(entry.audio_file.path, 'rb')),
            status=206 if range_header else 200,
            content_type=content_type
        )

        # Add streaming headers
        response['Accept-Ranges'] = 'bytes'
        if range_header:
            response['Content-Range'] = f'bytes {range_start}-{range_end}/{file_size}'
        response['Content-Length'] = str(length)
        response['Content-Disposition'] = f'attachment; filename="{entry.original_filename}"'
        
        return response

    @action(detail=True, methods=['patch'])
    def rename(self, request, pk=None):
        """Rename the audio file"""
        entry = self.get_object()
        new_name = request.data.get('original_filename')
        
        if not new_name:
            return Response(
                {'error': 'New filename is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        entry.original_filename = new_name
        entry.save()
        
        return Response({
            'id': entry.id,
            'original_filename': entry.original_filename
        })

    def retrieve(self, request, *args, **kwargs):
        entry = self.get_object()
        serializer = self.get_serializer(entry)
        data = serializer.data

        # Add paths for separated tracks if processing is completed
        if entry.processing_status == 'completed':
            output_dir = f"entry_{entry.id}_stems/{entry.model_version}/{entry.audio_file.url.split('/')[-1].split('.')[0]}"
            data['output_dir'] = output_dir
            data['duration'] = entry.duration
            data['tracks'] = {
                'original': entry.audio_file.url,
                'vocals': f"/media/audio_files/{output_dir}/vocals.wav",
                'drums': f"/media/audio_files/{output_dir}/drums.wav",
                'bass': f"/media/audio_files/{output_dir}/bass.wav",
                'other': f"/media/audio_files/{output_dir}/other.wav",
            }

        return Response(data)

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