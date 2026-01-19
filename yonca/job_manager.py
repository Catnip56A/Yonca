"""
Background job system for long-running tasks like content translation
"""
import threading
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import json

class JobStatus:
    """Job status constants"""
    QUEUED = 'queued'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'

class BackgroundJob:
    """Represents a background job"""

    def __init__(self, job_type: str, job_data: Dict[str, Any], job_function):
        self.id = str(uuid.uuid4())
        self.type = job_type
        self.data = job_data
        self.function = job_function
        self.status = JobStatus.QUEUED
        self.progress = 0
        self.message = ""
        self.result = None
        self.error = None
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'type': self.type,
            'status': self.status,
            'progress': self.progress,
            'message': self.message,
            'result': self.result,
            'error': self.error,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }

class JobManager:
    """Manages background jobs"""

    def __init__(self):
        self.jobs: Dict[str, BackgroundJob] = {}
        self.worker_thread = None
        self.running = False
        self.job_queue = []

    def start_worker(self):
        """Start the background worker thread"""
        if self.worker_thread and self.worker_thread.is_alive():
            return

        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        print("Background job worker started")

    def stop_worker(self):
        """Stop the background worker"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)

    def queue_job(self, job_type: str, job_data: Dict[str, Any], job_function) -> str:
        """Queue a new job and return its ID"""
        job = BackgroundJob(job_type, job_data, job_function)
        self.jobs[job.id] = job
        self.job_queue.append(job)
        print(f"Queued job {job.id} of type {job_type}")
        return job.id

    def get_job(self, job_id: str) -> Optional[BackgroundJob]:
        """Get job by ID"""
        return self.jobs.get(job_id)

    def get_all_jobs(self) -> Dict[str, Dict[str, Any]]:
        """Get all jobs as dictionaries"""
        return {job_id: job.to_dict() for job_id, job in self.jobs.items()}

    def _worker_loop(self):
        """Main worker loop that processes queued jobs"""
        while self.running:
            if self.job_queue:
                job = self.job_queue.pop(0)  # FIFO
                self._execute_job(job)
            else:
                time.sleep(1)  # Wait for jobs

    def _execute_job(self, job: BackgroundJob):
        """Execute a single job"""
        try:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now()
            print(f"Starting job {job.id}")

            # Execute the job function
            result = job.function(job)

            job.status = JobStatus.COMPLETED
            job.result = result
            job.progress = 100
            job.message = "Job completed successfully"
            job.completed_at = datetime.now()

            print(f"Completed job {job.id}")

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.now()
            print(f"Failed job {job.id}: {e}")

# Global job manager instance
job_manager = JobManager()