import { useRef, useState, useEffect } from 'react';
import { Slider } from '@/components/ui/slider';
import { Button } from '@/components/ui/button';
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Volume2,
  VolumeX
} from 'lucide-react';

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

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    // audio.onplay = () => {
    //   console.log('onplay');
    //   audio.currentTime = currentTime;
    //   setIsPlaying(true);
    // };
    // audio.onseeking = (e: Event) => {
    //   console.log('onseeking');
    //   audio.currentTime = (e.target as HTMLAudioElement).currentTime;
    //   setCurrentTime((e.target as HTMLAudioElement).currentTime);
    // // };
    // audio.onpause = () => {
    //   console.log('onpause');
    //   setIsPlaying(false);
    // };
    // audio.onplaying = () => {
    //   console.log('onplaying');
    //   setCurrentTime(audio.currentTime);
    // };
    audio.onloadedmetadata = () => {
      console.log('onloadedmetadata');
      setDuration(audio.duration);
    };
    audio.onended = () => {
      console.log('onended');
      if (currentTrackIndex < tracks.length - 1) {
        setCurrentTrackIndex(currentTrackIndex + 1);
      } else {
        setIsPlaying(false);
      }
    };
  }, [currentTrackIndex, tracks.length]);


  const handleVolumeChange = (value: number) => {
    if (audioRef.current) {
      audioRef.current.volume = value;
      setVolume(value);
      setIsMuted(value === 0);
    }
  };

  const toggleMute = () => {
    if (audioRef.current) {
      const newMuted = !isMuted;
      audioRef.current.volume = newMuted ? 0 : volume;
      setIsMuted(newMuted);
    }
  };

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const skipTrack = (direction: 'prev' | 'next') => {
    if (direction === 'prev') {
      setCurrentTrackIndex(Math.max(0, currentTrackIndex - 1));
    } else {
      setCurrentTrackIndex(Math.min(tracks.length - 1, currentTrackIndex + 1));
    }
  };

  return (
    <div className="p-4 bg-white rounded-lg shadow">
      <audio
        ref={audioRef}
        src={tracks[currentTrackIndex]?.url}
        onPlay={() => {
          console.log('onPlay', audioRef.current?.currentTime, currentTime);
          if (audioRef.current) {
            console.log('setting currentTime', currentTime);
            audioRef.current.currentTime = currentTime;
          }
          console.log('after onPlay', audioRef.current?.currentTime, currentTime);
          setIsPlaying(true);
        }}
        onPause={() => {
          console.log('onPause', audioRef.current?.currentTime, currentTime);
          setIsPlaying(false);
        }}
        crossOrigin="anonymous"
      >
        <track kind="captions" src="" />
      </audio>

      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-medium">
          {tracks[currentTrackIndex]?.name}
        </span>
        <div className="flex items-center gap-2">
          <span className="text-sm">{formatTime(currentTime)}</span>
          <span className="text-sm text-gray-500">/</span>
          <span className="text-sm">{formatTime(duration)}</span>
        </div>
      </div>

      <Slider
        value={[currentTime]}
        max={duration}
        step={1}
        onValueChange={(value: number[]) => {
          console.log('onValueChange', value);
          if (audioRef.current) {
            setCurrentTime(value[0]);
          }
        }}
        className="mb-4"
      />

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => skipTrack('prev')}
          >
            <SkipBack className="w-4 h-4" />
          </Button>

          <Button
            variant="outline"
            size="icon"
            onClick={() =>
              isPlaying ? audioRef.current?.pause() : audioRef.current?.play()
            }
          >
            {isPlaying ? (
              <Pause className="w-4 h-4" />
            ) : (
              <Play className="w-4 h-4" />
            )}
          </Button>

          <Button
            variant="ghost"
            size="icon"
            onClick={() => skipTrack('next')}
          >
            <SkipForward className="w-4 h-4" />
          </Button>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleMute}
          >
            {isMuted ? (
              <VolumeX className="w-4 h-4" />
            ) : (
              <Volume2 className="w-4 h-4" />
            )}
          </Button>
          <Slider
            value={[isMuted ? 0 : volume]}
            max={1}
            step={0.1}
            onValueChange={(value: number[]) => handleVolumeChange(value[0])}
            className="w-24"
          />
        </div>
      </div>
    </div>
  );
}; 