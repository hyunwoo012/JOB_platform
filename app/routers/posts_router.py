from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..deps import get_async_db, require_role
from ..models import User, UserRole, JobPost, JobPostImage, JobPostStatus
from ..schemas import (
    JobPostCreate,
    JobPostUpdate,
    JobPostOut,
    JobPostImageCreate,
    JobPostImageOut,
)

router = APIRouter(prefix="/job-posts", tags=["job-posts"])


# -------------------------------------------------
# 공고 생성 (회사만 가능)
# POST /api/job-posts
# -------------------------------------------------
@router.post("", response_model=JobPostOut)
async def create_job_post(
    payload: JobPostCreate,
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: AsyncSession = Depends(get_async_db),
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
    await db.commit()
    await db.refresh(job)
    return job


# -------------------------------------------------
# 공고 목록 조회
# GET /api/job-posts
# -------------------------------------------------
@router.get("", response_model=list[JobPostOut])
async def list_job_posts(
    db: AsyncSession = Depends(get_async_db),
    status: JobPostStatus | None = Query(default=None),
    region: str | None = Query(default=None),
):
    stmt = (
        select(JobPost)
        .where(JobPost.is_deleted == False)  # noqa: E712
        .order_by(JobPost.created_at.desc())
    )

    if status:
        stmt = stmt.where(JobPost.status == status)
    if region:
        stmt = stmt.where(JobPost.region == region)

    result = await db.execute(stmt)
    return result.scalars().all()


# -------------------------------------------------
# 공고 단건 조회
# GET /api/job-posts/{job_post_id}
# -------------------------------------------------
@router.get("/{job_post_id}", response_model=JobPostOut)
async def get_job_post(
    job_post_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    stmt = (
        select(JobPost)
        .where(
            JobPost.id == job_post_id,
            JobPost.is_deleted == False,  # noqa: E712
        )
    )

    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job post not found")

    return job


# -------------------------------------------------
# 공고 수정 (회사만 가능)
# PUT /api/job-posts/{job_post_id}
# -------------------------------------------------
@router.put("/{job_post_id}", response_model=JobPostOut)
async def update_job_post(
    job_post_id: int,
    payload: JobPostUpdate,
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: AsyncSession = Depends(get_async_db),
):
    job = await db.get(JobPost, job_post_id)

    if not job or job.is_deleted:
        raise HTTPException(status_code=404, detail="Job post not found")

    if job.company_id != user.id:
        raise HTTPException(status_code=403, detail="Not your job post")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(job, field, value)

    await db.commit()
    await db.refresh(job)
    return job


# -------------------------------------------------
# 공고 이미지 추가 (회사만 가능)
# POST /api/job-posts/{job_post_id}/images
# -------------------------------------------------
@router.post("/{job_post_id}/images", response_model=JobPostImageOut)
async def add_job_post_image(
    job_post_id: int,
    payload: JobPostImageCreate,
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: AsyncSession = Depends(get_async_db),
):
    job = await db.get(JobPost, job_post_id)

    if not job or job.is_deleted:
        raise HTTPException(status_code=404, detail="Job post not found")

    if job.company_id != user.id:
        raise HTTPException(status_code=403, detail="Not your job post")

    img = JobPostImage(
        job_post_id=job_post_id,
        image_url=payload.image_url,
    )
    db.add(img)
    await db.commit()
    await db.refresh(img)

    return img
