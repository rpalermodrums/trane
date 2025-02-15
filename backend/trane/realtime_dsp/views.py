from django.core.files.storage import FileSystemStorage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

from .serializers import FileUploadSerializer
from .tasks import process_audio_file, process_midi_events
from .models import ProcessingTask, ProcessingResult

class UploadFileAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, format=None):
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            # Save the file using Django's FileSystemStorage
            uploaded_file = serializer.validated_data['file']
            fs = FileSystemStorage()
            filename = fs.save(uploaded_file.name, uploaded_file)
            file_path = fs.path(filename)
            
            # Determine file type and schedule processing
            if filename.lower().endswith(('.wav', '.mp3', '.ogg')):
                task = process_audio_file.delay(file_path)
                file_type = 'audio'
            elif filename.lower().endswith('.mid'):
                task = process_midi_events.delay([], 0)  # simplified for now
                file_type = 'midi'
            else:
                return Response({'error': 'Unsupported file type'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create a ProcessingTask record so the frontend can later poll for results
            ProcessingTask.objects.create(
                task_id=task.id,
                task_type=file_type,
                status='pending'
            )
            
            return Response({
                'task_id': task.id,
                'file_type': file_type,
                'message': 'Processing started'
            }, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetResultAPIView(APIView):
    def get(self, request, task_id, format=None):
        try:
            task = ProcessingTask.objects.get(task_id=task_id)
            if task.status == 'completed':
                result = ProcessingResult.objects.get(task=task)
                return Response({
                    'status': 'completed',
                    'result': result.features
                })
            elif task.status == 'failed':
                return Response({
                    'status': 'failed',
                    'error': task.error_message
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({
                    'status': task.status,
                    'message': 'Task is still processing'
                })
        except ProcessingTask.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND) 