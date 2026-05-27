'use client'
import { useState } from 'react'
import LogUploader from '../../components/upload/LogUploader'

export default function UploadPage() {
  const [tab, setTab] = useState<'logs' | 'text'>('logs')

  return (
    <div className="flex-1 flex flex-col p-8 sm:p-20 max-w-4xl mx-auto w-full">
      <h1 className="text-3xl font-heading font-bold mb-8">Submit Pipeline for Audit</h1>
      
      <div className="flex border-b border-border mb-8">
        <button 
          className={`py-3 px-6 font-bold ${tab === 'logs' ? 'text-accent border-b-2 border-accent' : 'text-textSecondary'}`}
          onClick={() => setTab('logs')}
        >
          Upload logs (JSON)
        </button>
        <button 
          className={`py-3 px-6 font-bold ${tab === 'text' ? 'text-accent border-b-2 border-accent' : 'text-textSecondary'}`}
          onClick={() => setTab('text')}
        >
          Describe your pipeline
        </button>
      </div>

      <div className="bg-surface border border-border p-8 rounded-lg">
        {tab === 'logs' ? (
          <div>
             <LogUploader />
          </div>
        ) : (
          <div>
            <textarea 
               className="w-full h-48 bg-background border border-border p-4 rounded text-textPrimary focus:border-accent outline-none"
               placeholder="Describe your pipeline steps sequentially... E.g. 'I initialize a langchain loop taking 600ms, then I make a sync query to the DB...'"
            />
            <button className="mt-4 bg-accent text-black font-bold py-2 px-6 rounded hover:opacity-90">
              Submit Description
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
