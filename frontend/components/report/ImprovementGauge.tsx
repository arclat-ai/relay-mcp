import { RadialBarChart, RadialBar, ResponsiveContainer, PolarAngleAxis } from 'recharts';

export default function ImprovementGauge({ pct }: { pct: number }) {
  const data = [
    { name: 'Improvement', value: pct, fill: '#00FF88' },
  ];

  return (
    <div className="relative w-40 h-40 flex items-center justify-center">
       <div className="absolute inset-0 z-10 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold font-heading text-accent">~{pct}%</span>
          <span className="text-xs text-textSecondary uppercase tracking-widest mt-1">Faster</span>
       </div>
       <div className="absolute inset-0">
          <ResponsiveContainer width="100%" height="100%">
            <RadialBarChart cx="50%" cy="50%" innerRadius="70%" outerRadius="90%" barSize={10} data={data} startAngle={90} endAngle={-270}>
              <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
              <RadialBar background={{ fill: '#222' }} dataKey="value" cornerRadius={5} />
            </RadialBarChart>
          </ResponsiveContainer>
       </div>
    </div>
  )
}
