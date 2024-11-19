import { useEffect, useRef, useState } from 'react';
import WaveSurfer from 'wavesurfer.js';

interface WaveformVisualizerProps {
  audioUrl: string;
  currentTime: number;
  duration: number;
  onTimeChange: (time: number[]) => void;
}

export const WaveformVisualizer = ({
  audioUrl,
  currentTime,
  duration,
  onTimeChange,
}: WaveformVisualizerProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const wavesurferRef = useRef<WaveSurfer | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    if (!containerRef.current || !audioUrl) return;

    wavesurferRef.current = WaveSurfer.create({
      container: containerRef.current,
      waveColor: 'rgb(var(--foreground))',
      progressColor: 'rgb(var(--primary))',
      cursorColor: 'rgb(var(--primary))',
      barWidth: 2,
      barGap: 1,
      height: 60,
      normalize: true,
    });

    wavesurferRef.current.load(audioUrl);

    wavesurferRef.current.on('ready', () => {
      setIsReady(true);
    });

    wavesurferRef.current.on('interaction', (position: number): void => {
      onTimeChange([position * duration]);
    });

    return () => {
      if (wavesurferRef.current) {
        wavesurferRef.current.destroy();
      }
    };
  }, [audioUrl]);

  useEffect(() => {
    if (isReady && wavesurferRef.current) {
      wavesurferRef.current.seekTo(currentTime / duration);
    }
  }, [currentTime, duration, isReady]);

  return (
    <div ref={containerRef} className="w-full" />
  );
}; 