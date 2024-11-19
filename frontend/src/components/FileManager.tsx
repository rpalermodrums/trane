import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchAPI } from '@/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Download, 
  Trash2, 
  Edit2, 
  Music, 
  Calendar,
  Clock,
  HardDrive
} from 'lucide-react';
import { formatDistance } from 'date-fns';
import { bytesToSize } from '@/lib/utils';
import { toast } from '@/hooks/use-toast';

interface FileEntry {
  id: string;
  original_filename: string;
  file_size: number;
  created_at: string;
  duration: number;
  processing_status: string;
}

export const FileManager = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'date' | 'name' | 'size'>('date');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [newFileName, setNewFileName] = useState('');

  const queryClient = useQueryClient();

  const { data: files = [], isLoading } = useQuery({
    queryKey: ['files'],
    queryFn: () => fetchAPI('/entries/'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => fetchAPI(`/entries/${id}/`, {
      method: 'DELETE',
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['files'] });
      toast({
        title: 'File Deleted',
        description: 'The file has been successfully deleted.',
      });
    },
  });

  const renameMutation = useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) => 
      fetchAPI(`/entries/${id}/`, {
        method: 'PATCH',
        body: JSON.stringify({ original_filename: name }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['files'] });
      setEditingId(null);
      toast({
        title: 'File Renamed',
        description: 'The file has been successfully renamed.',
      });
    },
  });

  const handleRename = (id: string) => {
    const file = files.find((f: FileEntry) => f.id === id);
    if (file) {
      setNewFileName(file.original_filename);
      setEditingId(id);
    }
  };

  const submitRename = (id: string) => {
    if (newFileName.trim()) {
      renameMutation.mutate({ id, name: newFileName });
    }
  };

  const handleDownload = async (id: string) => {
    try {
      const response = await fetch(`/api/entries/${id}/download/`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = files.find((f: FileEntry) => f.id === id)?.original_filename || 'download';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      toast({
        title: 'Download Failed',
        description: 'Failed to download the file. Please try again.',
        variant: 'destructive',
      });
    }
  };

  const filteredFiles = files
    .filter((file: FileEntry) => 
      file.original_filename.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a: FileEntry, b: FileEntry) => {
      switch (sortBy) {
        case 'name':
          return a.original_filename.localeCompare(b.original_filename);
        case 'size':
          return b.file_size - a.file_size;
        default:
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      }
    });

  if (isLoading) {
    return <div className="flex justify-center p-8">Loading...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <Input
          type="search"
          placeholder="Search files..."
          value={searchTerm}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
          className="max-w-sm"
        />
        <select
          value={sortBy}
          onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSortBy(e.target.value as 'date' | 'name' | 'size')}
          className="border rounded p-2"
        >
          <option value="date">Sort by Date</option>
          <option value="name">Sort by Name</option>
          <option value="size">Sort by Size</option>
        </select>
      </div>

      <div className="grid gap-4">
        {filteredFiles.map((file: FileEntry) => (
          <div
            key={file.id}
            className="border rounded-lg p-4 flex items-center justify-between bg-card"
          >
            <div className="flex items-center gap-4">
              <Music className="h-8 w-8 text-primary" />
              <div>
                {editingId === file.id ? (
                  <div className="flex items-center gap-2">
                    <Input
                      value={newFileName}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewFileName(e.target.value)}
                      className="max-w-xs"
                    />
                    <Button
                      size="sm"
                      onClick={() => submitRename(file.id)}
                    >
                      Save
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setEditingId(null)}
                    >
                      Cancel
                    </Button>
                  </div>
                ) : (
                  <>
                    <h3 className="font-medium">{file.original_filename}</h3>
                    <div className="text-sm text-muted-foreground flex items-center gap-4">
                      <span className="flex items-center gap-1">
                        <Calendar className="h-4 w-4" />
                        {formatDistance(new Date(file.created_at), new Date(), { addSuffix: true })}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-4 w-4" />
                        {Math.round(file.duration)}s
                      </span>
                      <span className="flex items-center gap-1">
                        <HardDrive className="h-4 w-4" />
                        {bytesToSize(file.file_size)}
                      </span>
                    </div>
                  </>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="ghost"
                onClick={() => handleDownload(file.id)}
              >
                <Download className="h-4 w-4" />
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => handleRename(file.id)}
              >
                <Edit2 className="h-4 w-4" />
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  if (confirm('Are you sure you want to delete this file?')) {
                    deleteMutation.mutate(file.id);
                  }
                }}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}; 