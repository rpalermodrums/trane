import { useRef, useState, useEffect } from 'react';
import { Slider } from '@/components/ui/slider';
import { Button } from '@/components/ui/button';
import { WaveformVisualizer } from './WaveformVisualizer';
import { formatDuration } from '@/lib/utils';
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Volume2,
  VolumeX,
  RotateCcw,
} from 'lucide-react';
import { TrackControls } from './TrackControls';

interface Track {
  name: string;
  url: string;
}

interface AudioPlayerProps {
  tracks: Track[];
}

export const AudioPlayer = ({ tracks }: AudioPlayerProps) => {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [currentTrackIndex, setCurrentTrackIndex] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [isLooping, setIsLooping] = useState(false);
  const [trackVolumes, setTrackVolumes] = useState<{ [key: string]: number }>(
    tracks.reduce((acc, track) => ({ ...acc, [track.name]: 1 }), {})
  );
  const [soloedTrack, setSoloedTrack] = useState<string | null>(null);
  const [mutedTracks, setMutedTracks] = useState<Set<string>>(new Set());

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const updateTime = () => setCurrentTime(audio.currentTime);
    const updateDuration = () => setDuration(audio.duration);
    
    audio.addEventListener('timeupdate', updateTime);
    audio.addEventListener('loadedmetadata', updateDuration);
    audio.addEventListener('ended', handleTrackEnd);

    return () => {
      audio.removeEventListener('timeupdate', updateTime);
      audio.removeEventListener('loadedmetadata', updateDuration);
      audio.removeEventListener('ended', handleTrackEnd);
    };
  }, [currentTrackIndex]);

  const togglePlay = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleTrackEnd = () => {
    if (isLooping) {
      if (audioRef.current) {
        audioRef.current.currentTime = 0;
        audioRef.current.play();
      }
    } else if (currentTrackIndex < tracks.length - 1) {
      setCurrentTrackIndex(currentTrackIndex + 1);
    } else {
      setIsPlaying(false);
    }
  };

  const handleTimeChange = (value: number[]) => {
    if (audioRef.current) {
      audioRef.current.currentTime = value[0];
      setCurrentTime(value[0]);
    }
  };

  const handleVolumeChange = (value: number[]) => {
    if (audioRef.current) {
      const newVolume = value[0];
      audioRef.current.volume = newVolume;
      setVolume(newVolume);
      setIsMuted(newVolume === 0);
    }
  };

  const toggleMute = () => {
    if (audioRef.current) {
      const newMuted = !isMuted;
      audioRef.current.volume = newMuted ? 0 : volume;
      setIsMuted(newMuted);
    }
  };

  const changePlaybackRate = (rate: number) => {
    if (audioRef.current) {
      audioRef.current.playbackRate = rate;
      setPlaybackRate(rate);
    }
  };

  const toggleLoop = () => {
    setIsLooping(!isLooping);
    if (audioRef.current) {
      audioRef.current.loop = !isLooping;
    }
  };

  const handleTrackVolumeChange = (trackName: string, value: number) => {
    setTrackVolumes(prev => ({ ...prev, [trackName]: value }));
  };

  const toggleSolo = (trackName: string) => {
    if (soloedTrack === trackName) {
      setSoloedTrack(null);
    } else {
      setSoloedTrack(trackName);
    }
  };

  const toggleMuteTrack = (trackName: string) => {
    setMutedTracks(prev => {
      const newMuted = new Set(prev);
      if (newMuted.has(trackName)) {
        newMuted.delete(trackName);
      } else {
        newMuted.add(trackName);
      }
      return newMuted;
    });
  };

  return (
    <div className="p-4 bg-card rounded-lg shadow space-y-4">
      <audio
        ref={audioRef}
        src={tracks[currentTrackIndex]?.url}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
      />

      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">
          {tracks[currentTrackIndex]?.name}
        </span>
        <div className="flex items-center gap-2">
          <span className="text-sm">{formatDuration(currentTime)}</span>
          <span className="text-sm text-muted-foreground">/</span>
          <span className="text-sm">{formatDuration(duration)}</span>
        </div>
      </div>

      <WaveformVisualizer
        audioUrl={tracks[currentTrackIndex]?.url}
        currentTime={currentTime}
        duration={duration}
        onTimeChange={handleTimeChange}
      />

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setCurrentTrackIndex(Math.max(0, currentTrackIndex - 1))}
          >
            <SkipBack className="h-4 w-4" />
          </Button>

          <Button
            variant="outline"
            size="icon"
            onClick={togglePlay}
          >
            {isPlaying ? (
              <Pause className="h-4 w-4" />
            ) : (
              <Play className="h-4 w-4" />
            )}
          </Button>

          <Button
            variant="ghost"
            size="icon"
            onClick={() => setCurrentTrackIndex(Math.min(tracks.length - 1, currentTrackIndex + 1))}
          >
            <SkipForward className="h-4 w-4" />
          </Button>

          <Button
            variant="ghost"
            size="icon"
            onClick={toggleLoop}
            className={isLooping ? 'text-primary' : ''}
          >
            <RotateCcw className="h-4 w-4" />
          </Button>

          <select
            value={playbackRate}
            onChange={(e) => changePlaybackRate(Number(e.target.value))}
            className="border rounded p-1 text-sm"
          >
            <option value="0.5">0.5x</option>
            <option value="1">1x</option>
            <option value="1.5">1.5x</option>
            <option value="2">2x</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleMute}
          >
            {isMuted ? (
              <VolumeX className="h-4 w-4" />
            ) : (
              <Volume2 className="h-4 w-4" />
            )}
          </Button>
          <Slider
            value={[isMuted ? 0 : volume]}
            max={1}
            step={0.1}
            onValueChange={handleVolumeChange}
            className="w-24"
          />
        </div>
      </div>

      <div className="space-y-2">
        {tracks.map((track, index) => (
          <TrackControls
            key={track.name}
            track={track}
            volume={trackVolumes[track.name]}
            onVolumeChange={(value) => handleTrackVolumeChange(track.name, value)}
            isSolo={soloedTrack === track.name}
            isMuted={mutedTracks.has(track.name)}
            onSoloToggle={() => toggleSolo(track.name)}
            onMuteToggle={() => toggleMuteTrack(track.name)}
            isActive={currentTrackIndex === index}
          />
        ))}
      </div>
    </div>
  );
}; 