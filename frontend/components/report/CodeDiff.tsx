'use client'
// Simple CodeDiff since highlight.js adds bulk, we'll just format visually side-by-side for the MVP
export default function CodeDiff({ codeBefore, codeAfter }: { codeBefore: string, codeAfter: string }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
       <div className="bg-[#1e1e1e] border border-error/30 rounded overflow-hidden">
          <div className="bg-error/10 text-error text-xs px-4 py-2 border-b border-error/30 flex justify-between font-bold">
            <span>Before (slow)</span>
          </div>
          <pre className="p-4 overflow-x-auto text-sm font-mono text-gray-300">
             <code>{codeBefore}</code>
          </pre>
       </div>
       
       <div className="bg-[#1e1e1e] border border-[#7dd6f5]/30 rounded overflow-hidden">
          <div className="bg-[#7dd6f5]/10 text-accent text-xs px-4 py-2 border-b border-[#7dd6f5]/30 flex justify-between font-bold">
            <span>After (optimized)</span>
          </div>
          <pre className="p-4 overflow-x-auto text-sm font-mono text-gray-300">
             <code>{codeAfter}</code>
          </pre>
       </div>
    </div>
  )
}
