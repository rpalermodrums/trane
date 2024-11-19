import { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { fetchAPI } from '../api';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { AudioPlayer } from './AudioPlayer';

interface ProcessingOptions {
  model: string;
  instruments: string[];
}

export const AudioProcessor = () => {
  const [file, setFile] = useState<File | null>(null);
  const [options, setOptions] = useState<ProcessingOptions>({
    model: 'htdemucs',
    instruments: [],
  });
  const [progress, setProgress] = useState(0);
  const [processingStatus, setProcessingStatus] = useState<string | null>(null);
  const [socket, setSocket] = useState<WebSocket | null>(null);

  const processMutation = useMutation({
    mutationFn: async (formData: FormData) => {
      const response = await fetchAPI('/api/entries/', {
        method: 'POST',
        body: formData,
      });
      
      // Connect to WebSocket after successful task creation
      const ws = new WebSocket(
        `ws://${window.location.host}/ws/progress/${response.id}/`
      );
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setProgress(data.progress);
        setProcessingStatus(data.status);
        
        if (data.status === 'completed' || data.status === 'failed') {
          ws.close();
        }
      };
      
      setSocket(ws);
      return response;
    },
  });

  useEffect(() => {
    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, [socket]);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files[0]) {
      setFile(files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    const formData = new FormData();
    formData.append('audio_file', file);
    formData.append('model_version', options.model);
    formData.append('processing_options', JSON.stringify(options));

    processMutation.mutate(formData);
  };

  return (
    <div className="p-4">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">Audio File</label>
          <input
            type="file"
            accept="audio/*"
            onChange={handleFileChange}
            className="block w-full text-sm"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Model</label>
          <select
            value={options.model}
            onChange={(e) => setOptions({ ...options, model: e.target.value })}
            className="block w-full p-2 border rounded"
          >
            <option value="htdemucs">HTDemucs</option>
            <option value="mdx">MDX</option>
            <option value="htdemucs_6s">HTDemucs 6-stem</option>
          </select>
        </div>

        <Button type="submit" disabled={!file || processMutation.isPending}>
          {processMutation.isPending ? 'Processing...' : 'Process Audio'}
        </Button>

        {processMutation.isPending && (
          <Progress value={30} className="w-full" />
        )}

        {processingStatus && (
          <div className="mt-4">
            <div className="flex justify-between mb-2">
              <span className="text-sm font-medium">Processing Status</span>
              <span className="text-sm">{progress}%</span>
            </div>
            <Progress value={progress} className="w-full" />
          </div>
        )}

        {processingStatus === 'completed' && processMutation.data && (
          <AudioPlayer
            tracks={[
              {
                name: 'Original',
                url: processMutation.data.audio_file,
              },
              {
                name: 'Vocals',
                url: `${processMutation.data.output_dir}/vocals.wav`,
              },
              {
                name: 'Accompaniment',
                url: `${processMutation.data.output_dir}/accompaniment.wav`,
              },
            ]}
          />
        )}
      </form>
    </div>
  );
}; 