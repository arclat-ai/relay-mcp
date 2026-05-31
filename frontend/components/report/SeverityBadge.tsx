export default function SeverityBadge({ severity }: { severity: 'high' | 'medium' | 'low' | string }) {
  const colors = {
    high: 'bg-error text-white',
    medium: 'bg-warning text-white',
    low: 'bg-[#1a7a9e] text-white'
  }
  
  const selectedColor = colors[(severity || 'low').toLowerCase() as keyof typeof colors] || colors.low

  return (
    <span className={`text-[10px] uppercase font-bold tracking-wider px-2 py-1 rounded ${selectedColor}`}>
       {severity}
    </span>
  )
}
