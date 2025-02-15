import { FileUpload } from "@/components/file-upload"

function App () {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold mb-8">File Upload</h1>
      <FileUpload />
    </main>
  )
}

export default App