import * as React from "react"
import { useDropzone } from "react-dropzone"
import { UploadCloud, File, CheckCircle, XCircle } from "lucide-react"
import { Progress } from "@/components/ui/progress"
import { Button } from "@/components/ui/button"

interface FileWithProgress extends File {
  progress: number
  status: "uploading" | "success" | "error"
}

export function FileUpload() {
  const [files, setFiles] = React.useState<FileWithProgress[]>([])

  const onDrop = React.useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map((file) => ({
      ...file,
      progress: 0,
      status: "uploading" as const,
    }))
    setFiles((prevFiles) => [...prevFiles, ...newFiles])

    newFiles.forEach((file) => {
      simulateUpload(file)
    })
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop })

  const simulateUpload = (file: FileWithProgress) => {
    let progress = 0
    const interval = setInterval(() => {
      progress += 10
      setFiles((prevFiles) => prevFiles.map((f) => (f === file ? { ...f, progress: Math.min(progress, 100) } : f)))

      if (progress >= 100) {
        clearInterval(interval)
        setTimeout(() => {
          setFiles((prevFiles) => prevFiles.map((f) => (f === file ? { ...f, status: "success" } : f)))
        }, 500)
      }
    }, 500)
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
        <p className="mt-2 text-sm text-gray-600">Drag 'n' drop some files here, or click to select files</p>
      </div>

      {files.length > 0 && (
        <ul className="mt-4 space-y-2">
          {files.map((file, index) => (
            <li key={index} className="flex items-center justify-between p-2 bg-gray-100 rounded">
              <div className="flex items-center space-x-2">
                <File className="h-5 w-5 text-gray-500" />
                <span className="text-sm truncate max-w-[200px]">{file.name}</span>
              </div>
              <div className="flex items-center space-x-2">
                {file.status === "uploading" && <Progress value={file.progress} className="w-24" />}
                {file.status === "success" && <CheckCircle className="h-5 w-5 text-green-500" />}
                {file.status === "error" && <XCircle className="h-5 w-5 text-red-500" />}
              </div>
            </li>
          ))}
        </ul>
      )}

      <Button onClick={() => setFiles([])} className="mt-4" variant="outline" disabled={files.length === 0}>
        Clear Files
      </Button>
    </div>
  )
}

