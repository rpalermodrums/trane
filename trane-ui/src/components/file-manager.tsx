import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
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
  MoreVertical,
} from "lucide-react"
import React, { useState, useEffect } from "react"
import { Link } from "react-router"
import { FileUpload } from "./file-upload"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { ChevronDown } from "lucide-react"
// import { AudioCard } from "./audio-card"

// Navigation item component remains largely the same.
interface NavItemProps {
  href: string
  icon: React.ReactNode
  children: React.ReactNode
  active?: boolean
}

function NavItem({ href, icon, children, active }: NavItemProps) {
  return (
    <Link
      to={href}
      className={cn(
        "flex items-center gap-2 px-3 py-2 text-sm text-gray-700 rounded-lg",
        active && "bg-gray-100"
      )}
    >
      {icon}
      <span>{children}</span>
    </Link>
  )
}

function FolderItem({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link to={href} className="flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50">
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

// Updated AudioCard component with file type border and more actions.
function AudioCard({ title, metadata, waveform }: { title: string; metadata: string; waveform: string }) {
  const [isPlaying, setIsPlaying] = useState(false)

  const togglePlayback = () => {
    setIsPlaying(!isPlaying)
    // TODO: Implement actual audio playback
  }

  // Determine file type based on title extension
  const isMidi =
    title.toLowerCase().endsWith(".mid") || title.toLowerCase().endsWith(".midi")
  const borderColorClass = isMidi ? "border-l-4 border-yellow-500" : "border-l-4 border-blue-500"

  return (
    <div className={cn("group relative overflow-hidden rounded-lg border bg-white p-4", borderColorClass)}>
      <div className="flex justify-between items-center mb-2">
        <h3 className="font-medium text-gray-900">{title}</h3>
        <div className="flex gap-2">
          <Button variant="ghost" size="icon" onClick={togglePlayback}>
            {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          </Button>
          <Button variant="ghost" size="icon">
            <MoreVertical className="h-4 w-4 text-gray-600" />
          </Button>
        </div>
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

export default function FileManager() {
  // State for the task ID returned from the backend and for polling
  const [taskId, setTaskId] = useState<string | null>(null)
  const [pollStatus, setPollStatus] = useState<string>("")
  const [result, setResult] = useState<string | null>(null)

  // Start polling when a task ID is set
  useEffect(() => {
    if (!taskId) return
    setPollStatus("Processing file...")
    const intervalId = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8000/dsp/result/${taskId}/`)
        const data = await response.json()
        if (data.status === "completed") {
          clearInterval(intervalId)
          setPollStatus("Processing completed!")
          setResult(data.result)
        } else if (data.status === "failed") {
          clearInterval(intervalId)
          setPollStatus(`Processing failed: ${data.error}`)
        }
      } catch (error) {
        console.error("Error checking processing status:", error)
        clearInterval(intervalId)
        setPollStatus("Error checking processing status.")
      }
    }, 5000)
    return () => clearInterval(intervalId)
  }, [taskId])

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <div className="w-64 border-r mt-4 dark:bg-gray-900">
        <nav className="space-y-1 px-2">
          <NavItem href="/" icon={<LayoutGrid className="h-4 w-4" />} active>
            All Files
          </NavItem>
          <NavItem href="/audio" icon={<Waveform className="h-4 w-4" />}>
            Audio Files
          </NavItem>
          <NavItem href="/midi" icon={<Music className="h-4 w-4" />}>
            MIDI Files
          </NavItem>
          <details open className="px-2">
            <summary className="px-3 text-xs font-medium uppercase text-gray-500 cursor-pointer">
              Projects
            </summary>
            <div className="mt-2 space-y-1 pl-3">
              <FolderItem href="#">Song Demos</FolderItem>
              <FolderItem href="#">Podcast Episodes</FolderItem>
              <FolderItem href="#">Sound Effects</FolderItem>
              <FolderItem href="#">Instrument Samples</FolderItem>
            </div>
          </details>
        </nav>
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-y-auto">
        <header className="flex items-center justify-between border-b px-6 py-4">
          <div className="w-96">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
              <Input type="search" placeholder="Search files..." className="pl-9" />
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

        <div className="p-6 flex flex-col">
          {/* Primary Action Group */}
          <div className="space-y-6">
            <div className="flex items-center">
              <Button size="lg" className="gap-2 bg-primary text-primary-foreground">
                <Plus className="h-5 w-5" />
                New Project
              </Button>
              
              <div className="flex items-center ml-2 pl-2">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="lg" className="gap-2">
                      <Upload className="h-5 w-5" />
                      Upload
                      <ChevronDown className="h-4 w-4 opacity-50" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-48">
                    <DropdownMenuItem>
                      <Upload className="h-4 w-4 mr-2" />
                      Upload Audio
                    </DropdownMenuItem>
                    <DropdownMenuItem>
                      <Music className="h-4 w-4 mr-2" />
                      Upload MIDI
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem>
                      <Waveform className="h-4 w-4 mr-2" />
                      Analyze Audio
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
              
            </div>
            {/* File grid */}
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 m-6 py-6">
            <AudioCard title="Acoustic Guitar.wav" metadata="Audio • 3:42 • 44.1kHz" waveform="/placeholder.svg" />
            <AudioCard title="Drum Loop.mid" metadata="MIDI • 4 tracks • 120 BPM" waveform="/placeholder.svg" />
            <AudioCard title="Vocal Take 3.wav" metadata="Audio • 2:56 • 48kHz" waveform="/placeholder.svg" />
          </div>
          {/* Upload drop zone */}
          <div className="py-2">
            <FileUpload onUploadComplete={setTaskId} />
              </div>
    
              {/* Display processing status and result */}
              {pollStatus && (
                <div className="mb-4 p-4 rounded-lg bg-blue-100 text-blue-700">
                  {pollStatus}
                </div>
              )}
            {result && (
              <pre className="bg-gray-50 p-4 rounded-lg overflow-auto max-h-96">
                {JSON.stringify(result, null, 2)}
              </pre>
            )}
            </div>
          </div>

        </div>
      </div>
  )
}
