'use client'
import { useState, useRef } from 'react'

export default function LogUploader() {
  const [dragActive, setDragActive] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }
  
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0])
    }
  }
  
  return (
    <div 
      className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${dragActive ? 'border-accent bg-accent/5' : 'border-border bg-background'}`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
       {!file ? (
         <>
            <div className="mb-4 text-textSecondary">
               <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto text-border" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
               </svg>
            </div>
            <p className="font-bold text-lg mb-2">Drag and drop your logs</p>
            <p className="text-textSecondary text-sm">JSON format, max 10MB</p>
         </>
       ) : (
         <div>
            <p className="text-accent font-bold mb-2">File selected: {file.name}</p>
            <p className="text-textSecondary text-sm mb-6">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
            <button className="bg-accent text-black font-bold py-2 px-8 rounded hover:opacity-90">
               Audit logs
            </button>
         </div>
       )}
    </div>
  )
}
