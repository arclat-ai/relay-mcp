import asyncio
import uuid
import logging
from datetime import datetime, timezone
from celery import Celery
from sqlalchemy.future import select
from app.config import settings
from app.database import AsyncSessionLocal
from app.models.audit import Audit, AuditSummary
from app.models.bottleneck import Bottleneck
from app.models.recommendation import Recommendation
from app.engine.engine import AuditEngine

logger = logging.getLogger(__name__)

celery_app = Celery("audit_tasks", broker=settings.REDIS_URL)

def generate_report_html(result, pipeline_info) -> str:
    html = f"""
    <html>
    <head>
        <title>Arclat Audit Report</title>
        <style>
            body {{ font-family: sans-serif; background: #0a0a0a; color: #fff; padding: 20px; }}
            .card {{ background: #111; border: 1px solid #222; padding: 15px; margin-bottom: 20px; border-radius: 8px; }}
            h1, h2, h3 {{ color: #00FF88; }}
            .severity-high {{ background: #FF4444; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; }}
            .severity-medium {{ background: #FFAA00; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; }}
            .severity-low {{ background: #00AA44; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; }}
            pre {{ background: #000; padding: 10px; border-radius: 5px; overflow-x: auto; border: 1px solid #333; }}
        </style>
    </head>
    <body>
        <h1>Audit Report {pipeline_info}</h1>
        <div class="card">
            <h2>Summary</h2>
            <p><strong>Total Bottlenecks:</strong> {result.summary['total_bottlenecks']}</p>
            <p><strong>Estimated Improvement:</strong> ~{result.summary['estimated_improvement_pct']}% faster</p>
            <p><strong>Top Issue:</strong> {result.summary['top_issue']}</p>
        </div>
        <h2>Bottlenecks</h2>
    """
    
    for b in result.bottlenecks:
        html += f"""
        <div class="card">
            <h3>#{b.rank} {b.title} <span class="severity-{b.severity.lower()}">{b.severity.upper()}</span></h3>
            <p>{b.description}</p>
            <p><strong>Time Lost:</strong> {b.time_lost_ms} ms | <strong>Location:</strong> {b.location}</p>
            <hr style="border-color: #333;">
            <p><strong>Recommendation:</strong> {b.description}</p>
            <p>Effort: {b.effort} | Impact: {b.impact}</p>
            <h4>Before:</h4>
            <pre><code>{b.code_before}</code></pre>
            <h4>After:</h4>
            <pre><code>{b.code_after}</code></pre>
        </div>
        """
        
    html += "</body></html>"
    return html

async def _process_audit_async(audit_id_str: str):
    async with AsyncSessionLocal() as session:
        # 1. Fetch audit
        result = await session.execute(select(Audit).where(Audit.id == uuid.UUID(audit_id_str)))
        audit = result.scalar_one_or_none()
        
        if not audit:
            logger.error(f"Audit {audit_id_str} not found in DB")
            return
            
        try:
            # 2. Set status processing
            audit.status = "processing"
            await session.commit()
            
            # 3. Run AuditEngine
            engine = AuditEngine()
            
            # Simple fallback for storage URL fetching could be added later
            input_data = audit.input_raw
            if not input_data and audit.input_type == 'logs':
                # Stub: Fetch from Supabase storage using input_file_url
                input_data = "{}" # Normally fetch from storage 
            
            audit_result = engine.run(audit.input_type, input_data or "")
            
            # 4. Save each Finding as Bottleneck + Recommendation
            for finding in audit_result.bottlenecks:
                bottleneck = Bottleneck(
                    audit_id=audit.id,
                    type=finding.type,
                    severity=finding.severity,
                    title=finding.title,
                    description=finding.description,
                    time_lost_ms=finding.time_lost_ms,
                    location=finding.location,
                    rank=finding.rank
                )
                session.add(bottleneck)
                await session.flush() # flush to get bottleneck.id
                
                recommendation = Recommendation(
                    bottleneck_id=bottleneck.id,
                    title=finding.title,
                    explanation=finding.description, # Reuse description as explanation here
                    code_before=finding.code_before,
                    code_after=finding.code_after,
                    effort=finding.effort,
                    impact=finding.impact
                )
                session.add(recommendation)
                
            # 5-6. Save AuditSummary and Generate HTML
            report_html = generate_report_html(audit_result, str(audit.id))
            share_token = uuid.uuid4().hex
            
            summary = AuditSummary(
                audit_id=audit.id,
                total_bottlenecks=audit_result.summary['total_bottlenecks'],
                estimated_improvement_pct=audit_result.summary['estimated_improvement_pct'],
                top_issue=audit_result.summary['top_issue'],
                report_html=report_html,
                share_token=share_token
            )
            session.add(summary)
            
            # 7. Set status complete
            audit.status = "complete"
            audit.completed_at = datetime.now(timezone.utc)
            await session.commit()
            logger.info(f"Audit {audit_id_str} completed successfully")
            
        except Exception as e:
            logger.error(f"Audit {audit_id_str} failed: {str(e)}", exc_info=True)
            await session.rollback()

            # Re-fetch after rollback — the previous audit object is now detached
            result = await session.execute(select(Audit).where(Audit.id == uuid.UUID(audit_id_str)))
            audit = result.scalar_one_or_none()
            if audit:
                audit.status = "failed"
                await session.commit()

@celery_app.task
def run_audit(audit_id: str):
    logger.info(f"Starting async audit process for {audit_id}")
    asyncio.run(_process_audit_async(audit_id))
