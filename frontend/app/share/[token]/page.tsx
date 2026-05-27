'use client'
import AuditReportPage from '../../dashboard/[id]/page'

export default function SharedReport({ params }: { params: { token: string } }) {
  return (
    <div>
        <div className="bg-accent text-black text-center py-2 font-bold text-sm">
            Shared Public Report from Arclat
        </div>
        <AuditReportPage params={{id: params.token}} />
        <footer className="py-6 text-center text-textSecondary text-sm border-t border-border mt-10">
            Audited by Arclat &middot; arclat.com
        </footer>
    </div>
  )
}
