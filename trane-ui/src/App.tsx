import { useState, useEffect } from "react";
import FileManager from "@/components/file-manager"

function App() {
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    // Toggle the "dark" class on the document element based on darkMode state
    if (darkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [darkMode]);

  return (
    <div className="min-h-screen min-w-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      {/* Top header with branding and theme toggle on the right */}
      <header className="flex justify-between items-center p-4 border-b">
        <div>
          <h1 className="text-2xl font-bold">Trane</h1>
          <p className="text-sm text-gray-500">Real-Time Audio Analysis</p>
        </div>
        <button
          onClick={() => setDarkMode((prev) => !prev)}
          className="px-4 py-2 rounded bg-primary text-primary-foreground"
        >
          Toggle {darkMode ? "Light" : "Dark"} Mode
        </button>
      </header>
      <FileManager />
    </div>
  );
}

export default App
