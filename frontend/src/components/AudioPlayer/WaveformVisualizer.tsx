import { useEffect, useRef, useState } from 'react';
import WaveSurfer from 'wavesurfer.js';

interface WaveformVisualizerProps {
  height?: number;
  color?: string
  audioUrl: string;
  currentTime: number;
  duration: number;
  onTimeChange: (time: number[]) => void;
}

export const WaveformVisualizer = ({
  height = 60,
  color = '#6366f1',
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
      waveColor: color,
      progressColor: color,
      cursorColor: color,
      barWidth: 2,
      barGap: 1,
      height: height,
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
    if (isReady && wavesurferRef.current && duration > 0) {
      wavesurferRef.current.seekTo(currentTime / duration);
    }
  }, [currentTime, duration, isReady]);

  return (
    <div ref={containerRef} className="w-full" />
  );
}; 