import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { cn } from "@/lib/utils"
import {
  Bell,
  Grid,
  LayoutGrid,
  Plus,
  Search,
  Upload,
  AudioWaveformIcon as Waveform,
  Music,
  Play,
  Pause,
  Link,
} from "lucide-react"
import { useState } from "react"
import type React from "react"

interface NavItemProps {
  href: string
  icon: React.ReactNode
  children: React.ReactNode
  active?: boolean
}

function NavItem({ href, icon, children, active }: NavItemProps) {
  return (
    <Link
      href={href}
      className={cn("flex items-center gap-2 px-3 py-2 text-sm text-gray-700 rounded-lg", active && "bg-gray-100")}
    >
      {icon}
      <span>{children}</span>
    </Link>
  )
}

function FolderItem({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link href={href} className="flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50">
      <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
        />
      </svg>
      <span>{children}</span>
    </Link>
  )
}

function AudioCard({ title, metadata, waveform }: { title: string; metadata: string; waveform: string }) {
  const [isPlaying, setIsPlaying] = useState(false)

  const togglePlayback = () => {
    setIsPlaying(!isPlaying)
    // TODO: Implement actual audio playback
  }

  return (
    <div className="group relative overflow-hidden rounded-lg border bg-white p-4">
      <div className="flex justify-between items-center mb-2">
        <h3 className="font-medium text-gray-900">{title}</h3>
        <Button variant="ghost" size="icon" onClick={togglePlayback}>
          {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
        </Button>
      </div>
      <div className="aspect-[4/1] overflow-hidden mb-2">
        <img
          src={waveform || "/placeholder.svg"}
          alt="Audio waveform"
          width={400}
          height={100}
          className="h-full w-full object-cover"
        />
      </div>
      <p className="text-sm text-gray-500">{metadata}</p>
    </div>
  )
}

export default function AudioManager() {
  return (
    <div className="flex h-screen bg-white">
      {/* Sidebar */}
      <div className="w-64 border-r bg-white">
        <div className="p-4">
          <h1 className="text-xl font-bold">AudioLab</h1>
        </div>
        <nav className="space-y-1 px-2">
          <NavItem href="#" icon={<LayoutGrid className="h-4 w-4" />} active>
            All Files
          </NavItem>
          <NavItem href="#" icon={<Waveform className="h-4 w-4" />}>
            Audio Files
          </NavItem>
          <NavItem href="#" icon={<Music className="h-4 w-4" />}>
            MIDI Files
          </NavItem>
          <div className="py-3">
            <div className="px-3 text-xs font-medium uppercase text-gray-500">Projects</div>
            <div className="mt-2">
              <FolderItem href="#">Song Demos</FolderItem>
              <FolderItem href="#">Podcast Episodes</FolderItem>
              <FolderItem href="#">Sound Effects</FolderItem>
              <FolderItem href="#">Instrument Samples</FolderItem>
            </div>
          </div>
        </nav>
      </div>

      {/* Main content */}
      <div className="flex-1">
        <header className="flex items-center justify-between border-b px-6 py-4">
          <div className="w-96">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
              <Input type="search" placeholder="Search audio files..." className="pl-9" />
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon">
              <Grid className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon">
              <Bell className="h-4 w-4" />
            </Button>
            <div className="h-8 w-8 overflow-hidden rounded-full">
              <img
                src="/placeholder.svg"
                alt="Avatar"
                width={32}
                height={32}
                className="h-full w-full object-cover"
              />
            </div>
          </div>
        </header>

        <div className="p-6">
          <div className="mb-6 flex items-center gap-4">
            <Button className="gap-2">
              <Plus className="h-4 w-4" />
              New Project
            </Button>
            <Button variant="outline" className="gap-2">
              <Upload className="h-4 w-4" />
              Upload Audio
            </Button>
            <Button variant="outline" className="gap-2">
              <Music className="h-4 w-4" />
              Upload MIDI
            </Button>
            <Button variant="outline" className="gap-2">
              <Waveform className="h-4 w-4" />
              Analyze Audio
            </Button>
          </div>

          <div className="mb-6">
            <Tabs defaultValue="recent">
              <TabsList>
                <TabsTrigger value="recent">Recent</TabsTrigger>
                <TabsTrigger value="favorites">Favorites</TabsTrigger>
                <TabsTrigger value="shared">Shared</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            <AudioCard title="Acoustic Guitar.wav" metadata="Audio • 3:42 • 44.1kHz" waveform="/placeholder.svg" />
            <AudioCard title="Drum Loop.mid" metadata="MIDI • 4 tracks • 120 BPM" waveform="/placeholder.svg" />
            <AudioCard title="Vocal Take 3.wav" metadata="Audio • 2:56 • 48kHz" waveform="/placeholder.svg" />
          </div>
        </div>
      </div>
    </div>
  )
}

