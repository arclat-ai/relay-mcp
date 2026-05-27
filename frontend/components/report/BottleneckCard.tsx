import CodeDiff from './CodeDiff'
import SeverityBadge from './SeverityBadge'

export default function BottleneckCard({ bottleneck }: { bottleneck: any }) {
  return (
    <div className="bg-surface border border-border rounded-lg overflow-hidden flex flex-col p-6">
       <div className="flex justify-between items-start mb-4">
         <div className="flex items-center gap-4">
            <span className="bg-background text-textSecondary font-bold text-lg w-10 h-10 flex items-center justify-center rounded-full border border-border">
              #{bottleneck.rank}
            </span>
            <SeverityBadge severity={bottleneck.severity} />
         </div>
         <div className="text-right">
            <span className="text-error font-bold font-heading text-lg">+{bottleneck.time_lost_ms} ms</span>
            <p className="text-xs text-textSecondary uppercase tracking-widest mt-1">Time lost</p>
         </div>
       </div>
       
       <h3 className="text-xl font-bold text-white mb-2">{bottleneck.title}</h3>
       <p className="text-textSecondary mb-4 pb-4 border-b border-border">
         {bottleneck.description} <br/>
         <span className="inline-block mt-2 font-mono text-xs bg-background px-2 py-1 rounded">Loc: {bottleneck.location}</span>
       </p>

       <div>
          <div className="flex justify-between items-center mb-2">
            <h4 className="font-bold text-accent">Recommendation</h4>
            <div className="flex gap-3 text-xs font-bold uppercase tracking-wider">
               <span className="text-textSecondary">Effort: <span className="text-white">{bottleneck.effort}</span></span>
               <span className="text-textSecondary">Impact: <span className="text-accent">{bottleneck.impact}</span></span>
            </div>
          </div>
          
          <CodeDiff codeBefore={bottleneck.code_before} codeAfter={bottleneck.code_after} />
       </div>
    </div>
  )
}
