import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchAPI } from '../api';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { useDropzone } from 'react-dropzone';
import { useToast } from '@/hooks/use-toast';

interface ProcessingOptions {
  model: string;
  instruments: string[];
  priority?: 'low' | 'medium' | 'high';
}

export const AudioProcessor = () => {
  const { toast } = useToast();
  const [files, setFiles] = useState<File[]>([]);
  const [options, setOptions] = useState<ProcessingOptions>({
    model: 'htdemucs',
    instruments: [],
    priority: 'medium',
  });
  const [tasks, setTasks] = useState<Map<string, {
    progress: number;
    status: string;
  }>>(new Map());

  const queryClient = useQueryClient();

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'audio/*': ['.mp3', '.wav', '.flac', '.m4a', '.ogg']
    },
    onDrop: (acceptedFiles: File[]): void => {
      setFiles(prev => [...prev, ...acceptedFiles]); 
    },
    multiple: true,
    onDragEnter: () => {},
    onDragLeave: () => {},
    onDragOver: () => {}
  });

  const processMutation = useMutation({
    mutationFn: async (formData: FormData) => {
      try {
        const response = await fetchAPI('/entries/', {
          method: 'POST',
          body: formData,
        });
        
        // Connect WebSocket after task creation
        connectWebSocket(response.id);
        return response;
      } catch (error) {
        let errorMessage = 'An error occurred while processing the file.';
        if (error instanceof Error) {
          try {
            const errorData = JSON.parse(error.message);
            errorMessage = Object.entries(errorData)
              .map(([key, value]) => `${key}: ${value}`)
              .join(', ');
          } catch (e) {
            errorMessage = error.message;
          }
        }
        toast({
          title: 'Upload Failed',
          description: errorMessage,
          variant: 'destructive',
        });
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['entries'] });
      toast({
        title: 'Processing Started',
        description: 'Your audio files are being processed.',
      });
    },
  });

  const connectWebSocket = (taskId: string) => {
    const ws = new WebSocket(
      `ws://${window.location.host}/ws/progress/${taskId}/`
    );
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setTasks(prev => new Map(prev).set(taskId, {
        progress: data.progress,
        status: data.status,
      }));
      
      if (data.status === 'completed') {
        toast({
          title: 'Processing Complete',
          description: `Task ${taskId} has finished processing.`,
        });
      } else if (data.status === 'failed') {
        toast({
          title: 'Processing Failed',
          description: `Task ${taskId} failed: ${data.error}`,
          variant: 'destructive',
        });
      }
    };

    return ws;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (files.length === 0) return;

    for (const file of files) {
      const formData = new FormData();
      formData.append('audio_file', file);
      formData.append('model_version', options.model);
      formData.append('processing_options', JSON.stringify({
        ...options,
        filename: file.name,
      }));

      processMutation.mutate(formData);
    }
  };

  return (
    <div className="p-4 space-y-6">
      <div 
        {...getRootProps()} 
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
          ${isDragActive ? 'border-primary bg-primary/10' : 'border-gray-300'}`}
      >
        <input type="file" accept="audio/*" multiple {...getInputProps()} />
        <p>Drag & drop audio files here, or click to select files</p>
        <p className="text-sm text-gray-500">
          Supports MP3, WAV, FLAC, M4A, and OGG
        </p>
      </div>

      {files.length > 0 && (
        <div className="space-y-4">
          <h3 className="font-semibold">Selected Files ({files.length})</h3>
          {files.map((file, index) => (
            <div key={file.name} className="flex items-center justify-between">
              <span>{file.name}</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setFiles(files.filter((_, i) => i !== index))}
              >
                Remove
              </Button>
            </div>
          ))}
        </div>
      )}

      <div className="space-y-4">
        <div>
          <label htmlFor="model" className="block mb-2 text-sm font-medium">Model</label>
          <select
            id="model"
            value={options.model}
            onChange={(e) => setOptions({ ...options, model: e.target.value })}
            className="block w-full p-2 bg-white border rounded"
          >
            <option value="htdemucs">HTDemucs</option>
            <option value="mdx">MDX</option>
            <option value="htdemucs_6s">HTDemucs 6-stem</option>
          </select>
        </div>

        <div>
          <label htmlFor="priority" className="block mb-2 text-sm font-medium">Priority</label>
          <select
            id="priority"
            value={options.priority}
            onChange={(e) => setOptions({ 
              ...options, 
              priority: e.target.value as ProcessingOptions['priority'] 
            })}
            className="block w-full p-2 bg-white border rounded"
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </div>

        <Button 
          type="submit" 
          onClick={handleSubmit}
          disabled={files.length === 0 || processMutation.isPending}
        >
          {processMutation.isPending ? 'Processing...' : 'Process Files'}
        </Button>
      </div>

      {Array.from(tasks.entries()).map(([taskId, task]) => (
        <div key={taskId} className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Task {taskId}</span>
            <span>{task.status}</span>
          </div>
          <Progress value={task.progress} className="w-full" />
        </div>
      ))}
    </div>
  );
}; 