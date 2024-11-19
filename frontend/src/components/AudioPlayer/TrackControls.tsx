import { Slider } from '@/components/ui/slider';
import { Button } from '@/components/ui/button';
import { Volume2, VolumeX, Headphones } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TrackControlsProps {
  track: {
    name: string;
    url: string;
  };
  volume: number;
  onVolumeChange: (value: number) => void;
  isSolo: boolean;
  isMuted: boolean;
  onSoloToggle: () => void;
  onMuteToggle: () => void;
  isActive: boolean;
}

export const TrackControls = ({
  track,
  volume,
  onVolumeChange,
  isSolo,
  isMuted,
  onSoloToggle,
  onMuteToggle,
  isActive,
}: TrackControlsProps) => {
  return (
    <div className={cn(
      'flex items-center justify-between p-2 rounded',
      isActive && 'bg-accent',
      isMuted && 'opacity-50'
    )}>
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium">{track.name}</span>
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={onSoloToggle}
          className={cn(isSolo && 'text-primary')}
        >
          <Headphones className="h-4 w-4" />
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={onMuteToggle}
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
          onValueChange={(value) => onVolumeChange(value[0])}
          className="w-24"
        />
      </div>
    </div>
  );
}; 