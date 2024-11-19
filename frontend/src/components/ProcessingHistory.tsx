import { useQuery } from '@tanstack/react-query';
import { fetchAPI } from '../api';

interface Entry {
  id: number;
  audio_file: string;
  processing_status: string;
  created_at: string;
  model_version: string;
}

export const ProcessingHistory = () => {
  const { data: entries, isLoading } = useQuery({
    queryKey: ['entries'],
    queryFn: () => fetchAPI('/entries/'),
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Processing History</h2>
      <div className="space-y-4">
        {entries?.map((entry: Entry) => (
          <div
            key={entry.id}
            className="border p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow"
          >
            <div className="flex justify-between items-center">
              <div>
                <h3 className="font-semibold">Task #{entry.id}</h3>
                <p className="text-sm text-gray-600">
                  Model: {entry.model_version}
                </p>
              </div>
              <div className="text-right">
                <span className={`inline-block px-2 py-1 rounded text-sm ${
                  entry.processing_status === 'completed'
                    ? 'bg-green-100 text-green-800'
                    : entry.processing_status === 'failed'
                    ? 'bg-red-100 text-red-800'
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {entry.processing_status}
                </span>
                <p className="text-xs text-gray-500 mt-1">
                  {new Date(entry.created_at).toLocaleString()}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}; 