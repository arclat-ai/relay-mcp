'use client'
import { useState } from 'react'

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
      className={`rounded-[1.75rem] border-2 border-dashed p-10 text-center transition-colors sm:p-12 ${dragActive ? 'border-accent bg-accent/10' : 'border-white/10 bg-white/5'}`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
       {!file ? (
         <>
            <div className="mb-5 text-textSecondary">
              <svg xmlns="http://www.w3.org/2000/svg" className="mx-auto h-12 w-12 text-accent/80" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
               </svg>
            </div>
            <p className="mb-2 text-lg font-semibold text-white">Drag and drop your logs</p>
            <p className="text-sm text-textSecondary">JSON format, max 10MB</p>
         </>
       ) : (
         <div>
            <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/15 text-accent">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <p className="mb-2 font-semibold text-white">File selected: {file.name}</p>
            <p className="mb-6 text-sm text-textSecondary">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
            <button className="rounded-full bg-accent px-8 py-3 font-semibold text-black transition-transform hover:-translate-y-0.5">
               Audit logs
            </button>
         </div>
       )}
    </div>
  )
}
