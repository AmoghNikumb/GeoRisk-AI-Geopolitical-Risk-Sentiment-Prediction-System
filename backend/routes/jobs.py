"""
routes/jobs.py
──────────────
GET  /api/jobs/status          — list all scheduler jobs and their state
POST /api/jobs/run/{job_name}  — manually trigger a named job
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime

router = APIRouter()

# Map of job names to their scheduler functions
JOB_REGISTRY = {
    "market":    "scheduler.job_market",
    "gdelt":     "scheduler.job_gdelt",
    "reddit":    "scheduler.job_reddit",
    "twitter":   "scheduler.job_twitter",
    "scoring":   "scheduler.job_process_and_score",
    "aggregate": "scheduler.job_aggregate",
    "risk":      "scheduler.job_risk_scores",
    "alerts":    "scheduler.job_alerts",
    "briefs":    "scheduler.job_briefs",
    "seed":      "seed_demo.run_seed",
}


@router.get("/jobs/status")
def get_jobs_status():
    """Returns status of all registered scheduler jobs."""
    try:
        from scheduler import _scheduler
        if _scheduler is None or not _scheduler.running:
            return {"scheduler_running": False, "jobs": []}

        jobs = []
        for job in _scheduler.get_jobs():
            next_run = job.next_run_time
            jobs.append({
                "id": job.id,
                "name": job.name or job.id,
                "next_run": next_run.isoformat() if next_run else None,
                "trigger": str(job.trigger),
                "status": "scheduled" if next_run else "paused",
            })
        return {
            "scheduler_running": True,
            "job_count": len(jobs),
            "jobs": jobs,
            "checked_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"scheduler_running": False, "error": str(e), "jobs": []}


@router.post("/jobs/run/{job_name}")
def run_job(job_name: str):
    """Manually trigger a named background job."""
    if job_name not in JOB_REGISTRY:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown job '{job_name}'. Available: {list(JOB_REGISTRY.keys())}",
        )

    import importlib
    module_path, func_name = JOB_REGISTRY[job_name].rsplit(".", 1)
    try:
        mod = importlib.import_module(module_path)
        func = getattr(mod, func_name)
        result = func()
        return {
            "job": job_name,
            "status": "completed",
            "result": str(result),
            "ran_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job '{job_name}' failed: {e}")
