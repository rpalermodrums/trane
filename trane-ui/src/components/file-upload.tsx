import * as React from "react"
import { useDropzone } from "react-dropzone"
import { UploadCloud, File as FileIcon, CheckCircle, XCircle, ArrowDown } from "lucide-react"
import { Progress } from "@/components/ui/progress"
import { Button } from "@/components/ui/button"

interface FileWithProgress {
  file: File;
  progress: number;
  status: "uploading" | "success" | "error";
}

interface FileUploadProps {
  onUploadComplete?: (taskId: string) => void;
}

export function FileUpload({ onUploadComplete }: FileUploadProps) {
  const [files, setFiles] = React.useState<FileWithProgress[]>([])

  const onDrop = React.useCallback((acceptedFiles: File[]) => {
    // Wrap each File in an object with extra properties
    const newFiles = acceptedFiles.map((file) => ({
      file,
      progress: 0,
      status: "uploading" as const,
    }))
    setFiles((prevFiles) => [...prevFiles, ...newFiles])

    newFiles.forEach((fileWrapper) => {
      simulateUpload(fileWrapper)
    })
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop })

  const simulateUpload = (fileWrapper: FileWithProgress) => {
    let progress = 0
    const interval = setInterval(() => {
      progress += 10
      setFiles((prevFiles) =>
        prevFiles.map((f) =>
          f === fileWrapper ? { ...f, progress: Math.min(progress, 100) } : f
        )
      )

      if (progress >= 100) {
        clearInterval(interval)
        setTimeout(() => {
          setFiles((prevFiles) =>
            prevFiles.map((f) =>
              f === fileWrapper ? { ...f, status: "success" } : f
            )
          )
        }, 500)
      }
    }, 500)
  }

  const handleUpload = () => {
    console.log("Uploading files:", files)
    const formData = new FormData()
    // Append the actual File instance by accessing the 'file' property
    if (files.length > 0) {
      formData.append("file", files[0].file)
    }
    fetch("http://localhost:8000/dsp/upload/", {
      method: "POST",
      headers: {
        // Do not manually set Content-Type header (the browser will set it)
        "Accept": "application/json"
      },
      body: formData,
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        return response.json()
      })
      .then((data) => {
        console.log("Upload response:", data)
        // Optionally update file status based on response
        setFiles(prevFiles =>
          prevFiles.map(f => f === files[0] ? { ...f, status: "success" } : f)
        )
        if (onUploadComplete) {
          onUploadComplete(data.task_id)
        }
      })
      .catch((error) => {
        console.error("Error uploading files:", error)
        setFiles(prevFiles =>
          prevFiles.map(f => f === files[0] ? { ...f, status: "error" } : f)
        )
      })
  }

  return (
    <div className="w-full max-w-md mx-auto">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive ? "border-primary bg-primary/10" : "border-gray-300"
        }`}
      >
        <input {...getInputProps()} />
        <UploadCloud className="mx-auto h-12 w-12 text-gray-400" />
        <p className="mt-2 text-sm text-gray-600">
          Drag &amp; drop files here, or click to select files
        </p>
        <ArrowDown className="mx-auto mt-2 h-6 w-6 text-gray-400 animate-bounce" />
      </div>

      {files.length > 0 && (
        <ul className="mt-4 space-y-2">
          {files.map((fileWrapper, index) => (
            <li key={index} className="flex items-center justify-between p-2 bg-gray-100 rounded">
              <div className="flex items-center space-x-2">
                <FileIcon className="h-5 w-5 text-gray-500" />
                <span className="text-sm truncate max-w-[200px]">{fileWrapper.file.name}</span>
              </div>
              <div className="flex items-center space-x-2">
                {fileWrapper.status === "uploading" && (
                  <Progress value={fileWrapper.progress} className="w-24" />
                )}
                {fileWrapper.status === "success" && (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                )}
                {fileWrapper.status === "error" && (
                  <XCircle className="h-5 w-5 text-red-500" />
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      <div className="flex gap-2 mt-4">
        <Button 
          onClick={handleUpload} 
          className="flex-1"
          variant="default"
          disabled={files.length === 0}
        >
          Upload Files
        </Button>
        <Button 
          onClick={() => setFiles([])} 
          variant="outline"
          disabled={files.length === 0}
        >
          Clear
        </Button>
      </div>
    </div>
  )
}

