'use client'
// Dashboard audit report viewer
import ImprovementGauge from '../../../components/report/ImprovementGauge'
import BottleneckCard from '../../../components/report/BottleneckCard'

export default function AuditReportPage({ params }: { params: { id: string } }) {
  // Stub for TanStack query poller
  const isComplete = true
  
  if (!isComplete) {
    return <div className="p-20 text-center animate-pulse">Analyzing your pipeline...</div>
  }

  // Stub data
  const summary = { total_bottlenecks: 5, estimated_improvement_pct: 35, top_issue: "Enable streaming output" }
  const dummyBottlenecks = [
    {
       rank: 1, severity: 'high', title: 'Enable streaming output', 
       description: 'Stream tokens as they are generated...', time_lost_ms: 2000, 
       location: 'llm_call_a', effort: 'low', impact: 'high', code_before: 'old', code_after: 'new'
    }
  ]

  return (
    <div className="p-8 sm:p-20 max-w-5xl mx-auto">
       <div className="flex justify-between items-center mb-8">
         <h1 className="text-3xl font-heading font-bold">Audit Report</h1>
         <button className="bg-surface border border-border px-4 py-2 rounded text-sm hover:bg-border transition-colors">
            Share report
         </button>
       </div>
       
       <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          <div className="md:col-span-2 bg-surface p-6 rounded border border-border flex items-center justify-between">
            <div>
              <h3 className="text-xl font-bold text-accent mb-2">Summary</h3>
              <p className="text-textSecondary">We found <strong className="text-white">{summary.total_bottlenecks} bottlenecks</strong>.</p>
              <p className="text-textSecondary mt-2">Top issue: <strong className="text-white">{summary.top_issue}</strong></p>
            </div>
          </div>
          <div className="bg-surface p-6 rounded border border-border flex flex-col items-center justify-center">
             <ImprovementGauge pct={summary.estimated_improvement_pct} />
          </div>
       </div>

       <h2 className="text-2xl font-bold mb-6">Bottlenecks</h2>
       <div className="flex flex-col gap-6">
          {dummyBottlenecks.map(b => (
            <BottleneckCard key={b.rank} bottleneck={b} />
          ))}
       </div>
    </div>
  )
}
