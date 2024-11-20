import { useParams } from '@tanstack/react-router';
import { useQuery } from '@tanstack/react-query';
import { fetchAPI } from '../api';
import { AudioPlayer } from '../components/AudioPlayer';
import { WaveformVisualizer } from '../components/AudioPlayer/WaveformVisualizer';
import { useState } from 'react';

interface Track {
  name: string;
  url: string;
  duration?: number;
  isSolo?: boolean;
  isMuted?: boolean;
  volume?: number;
}

export const PlaybackView = () => {
  const { entryId } = useParams({ from: '/protected/playback/$entryId' });
  const [currentTime, setCurrentTime] = useState<number>(0);
  const { data: entry, isLoading } = useQuery({
    queryKey: ['entries', entryId],
    queryFn: () => fetchAPI(`/entries/${entryId}/`),
  });
  console.log(entry?.tracks);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!entry) {
    return <div>Entry not found</div>;
  }

  const tracks: Track[] = [
    {
      name: 'Original',
      url: entry.tracks.original,
    },
    ...(entry.tracks.vocals ? [{
      name: 'Vocals',
      url: entry.tracks.vocals,
    }] : []),
    ...(entry.tracks.drums ? [{
      name: 'Drums',
      url: entry.tracks.drums,
    }] : []),
    ...(entry.tracks.bass ? [{
      name: 'Bass',
      url: entry.tracks.bass,
    }] : []),
    ...(entry.tracks.other ? [{
      name: 'Other',
      url: entry.tracks.other,
    }] : []),
  ].filter(track => track.url);

  return (
    <div className="container py-8 mx-auto">
      <h1 className="mb-6 text-2xl font-bold">Playback - Entry #{entryId}</h1>
      
      <div className="space-y-8">
        {tracks.map((track) => (
          <div key={track.name} className="space-y-2">
            <h3 className="font-medium">{track.name}</h3>
            <WaveformVisualizer
              audioUrl={track.url}
              height={80}
              color={
                track.name === 'Vocals' ? '#2563eb' :
                track.name === 'Drums' ? '#dc2626' :
                track.name === 'Bass' ? '#16a34a' :
                track.name === 'Other' ? '#7c3aed' :
                '#6366f1'
              }
              currentTime={Number.isFinite(currentTime) ? currentTime : 0}
              duration={entry.duration ?? 0}
              onTimeChange={(time) => {
                if (Array.isArray(time) && time.length > 0 && Number.isFinite(time[0])) {
                  setCurrentTime(time[0]);
                }
              }}
            />
          </div>
        ))}
        
        <AudioPlayer
          tracks={tracks}
        />
      </div>
    </div>
  );
}; 