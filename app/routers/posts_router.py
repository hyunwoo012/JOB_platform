from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from ..deps import get_db, get_current_user, require_role
from ..models import User, UserRole, JobPost, JobPostImage, JobPostStatus
from ..schemas import (
    JobPostCreate,
    JobPostUpdate,
    JobPostOut,
    JobPostImageCreate,
    JobPostImageOut,
)

router = APIRouter(prefix="/job-posts", tags=["job-posts"])


@router.post("", response_model=JobPostOut)
def create_job_post(
    payload: JobPostCreate,
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
):
    job = JobPost(
        company_id=user.id,
        title=payload.title,
        wage=payload.wage,
        description=payload.description,
        region=payload.region,
        status=payload.status,
        is_deleted=False,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("", response_model=list[JobPostOut])
def list_job_posts(
    db: Session = Depends(get_db),
    status: JobPostStatus | None = Query(default=None),
    region: str | None = Query(default=None),
):
    q = (
        db.query(JobPost)
        .options(joinedload(JobPost.images))
        .filter(JobPost.is_deleted == False)  # noqa: E712
    )
    if status:
        q = q.filter(JobPost.status == status)
    if region:
        q = q.filter(JobPost.region == region)

    jobs = q.order_by(JobPost.created_at.desc()).all()
    return jobs


@router.get("/{job_post_id}", response_model=JobPostOut)
def get_job_post(job_post_id: int, db: Session = Depends(get_db)):
    job = (
        db.query(JobPost)
        .options(joinedload(JobPost.images))
        .filter(JobPost.id == job_post_id, JobPost.is_deleted == False)  # noqa: E712
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job post not found")
    return job


@router.put("/{job_post_id}", response_model=JobPostOut)
def update_job_post(
    job_post_id: int,
    payload: JobPostUpdate,
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
):
    job = db.get(JobPost, job_post_id)
    if not job or job.is_deleted:
        raise HTTPException(status_code=404, detail="Job post not found")
    if job.company_id != user.id:
        raise HTTPException(status_code=403, detail="Not your job post")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)
    return job


@router.post("/{job_post_id}/images", response_model=JobPostImageOut)
def add_job_post_image(
    job_post_id: int,
    payload: JobPostImageCreate,
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
):
    job = db.get(JobPost, job_post_id)
    if not job or job.is_deleted:
        raise HTTPException(status_code=404, detail="Job post not found")
    if job.company_id != user.id:
        raise HTTPException(status_code=403, detail="Not your job post")

    img = JobPostImage(job_post_id=job_post_id, image_url=payload.image_url)
    db.add(img)
    db.commit()
    db.refresh(img)
    return img
