from fastapi import APIRouter, Depends, HTTPException, Query  # 라우터/의존성/예외/쿼리
from sqlalchemy.ext.asyncio import AsyncSession  # 비동기 세션
from sqlalchemy import select  # SQLAlchemy 조회

from ..deps import get_async_db, require_role  # DB 의존성/권한
from ..models import User, UserRole, JobPost, JobPostImage, JobPostStatus  # 모델
from ..schemas import (  # 스키마
    JobPostCreate,  # 공고 생성
    JobPostUpdate,  # 공고 수정
    JobPostOut,  # 공고 응답
    JobPostImageCreate,  # 이미지 생성
    JobPostImageOut,  # 이미지 응답
)

router = APIRouter(prefix="/job-posts", tags=["job-posts"])  # /job-posts 라우터


# -------------------------------------------------
# 공고 생성 (회사만 가능)
# POST /api/job-posts
# -------------------------------------------------
@router.post("", response_model=JobPostOut)  # 공고 생성
async def create_job_post(  # 핸들러
    payload: JobPostCreate,  # 요청 바디
    user: User = Depends(require_role(UserRole.COMPANY)),  # 회사만
    db: AsyncSession = Depends(get_async_db),  # DB 세션
):
    job = JobPost(  # 공고 객체 생성
        company_id=user.id,  # 회사 ID
        title=payload.title,  # 제목
        wage=payload.wage,  # 시급/급여
        description=payload.description,  # 설명
        region=payload.region,  # 지역
        status=payload.status,  # 상태
        is_deleted=False,  # 삭제 여부
    )
    db.add(job)  # 세션 추가
    await db.commit()  # 커밋
    await db.refresh(job)  # DB 반영
    return job  # 공고 반환


# -------------------------------------------------
# 공고 목록 조회
# GET /api/job-posts
# -------------------------------------------------
@router.get("", response_model=list[JobPostOut])  # 공고 목록
async def list_job_posts(  # 핸들러
    db: AsyncSession = Depends(get_async_db),  # DB 세션
    status: JobPostStatus | None = Query(default=None),  # 상태 필터
    region: str | None = Query(default=None),  # 지역 필터
):
    stmt = (  # 기본 쿼리
        select(JobPost)  # 공고 조회
        .where(JobPost.is_deleted == False)  # 삭제 제외  # noqa: E712
        .order_by(JobPost.created_at.desc())  # 최신순
    )

    if status:  # 상태 필터
        stmt = stmt.where(JobPost.status == status)  # 상태 조건
    if region:  # 지역 필터
        stmt = stmt.where(JobPost.region == region)  # 지역 조건

    result = await db.execute(stmt)  # 조회 실행
    return result.scalars().all()  # 목록 반환


# -------------------------------------------------
# 공고 단건 조회
# GET /api/job-posts/{job_post_id}
# -------------------------------------------------
@router.get("/{job_post_id}", response_model=JobPostOut)  # 공고 단건
async def get_job_post(  # 핸들러
    job_post_id: int,  # 공고 ID
    db: AsyncSession = Depends(get_async_db),  # DB 세션
):
    stmt = (  # 조회 쿼리
        select(JobPost)  # 공고 조회
        .where(  # 조건
            JobPost.id == job_post_id,  # ID 일치
            JobPost.is_deleted == False,  # 삭제 제외  # noqa: E712
        )
    )

    result = await db.execute(stmt)  # 조회 실행
    job = result.scalar_one_or_none()  # 단일 공고

    if not job:  # 없으면
        raise HTTPException(status_code=404, detail="Job post not found")  # 404

    return job  # 공고 반환


# -------------------------------------------------
# 공고 수정 (회사만 가능)
# PUT /api/job-posts/{job_post_id}
# -------------------------------------------------
@router.put("/{job_post_id}", response_model=JobPostOut)  # 공고 수정
async def update_job_post(  # 핸들러
    job_post_id: int,  # 공고 ID
    payload: JobPostUpdate,  # 요청 바디
    user: User = Depends(require_role(UserRole.COMPANY)),  # 회사만
    db: AsyncSession = Depends(get_async_db),  # DB 세션
):
    job = await db.get(JobPost, job_post_id)  # 공고 조회

    if not job or job.is_deleted:  # 없거나 삭제됨
        raise HTTPException(status_code=404, detail="Job post not found")  # 404

    if job.company_id != user.id:  # 소유자 확인
        raise HTTPException(status_code=403, detail="Not your job post")  # 권한 오류

    for field, value in payload.model_dump(exclude_unset=True).items():  # 변경 필드 순회
        setattr(job, field, value)  # 값 반영

    await db.commit()  # 커밋
    await db.refresh(job)  # DB 반영
    return job  # 공고 반환


# -------------------------------------------------
# 공고 이미지 추가 (회사만 가능)
# POST /api/job-posts/{job_post_id}/images
# -------------------------------------------------
@router.post("/{job_post_id}/images", response_model=JobPostImageOut)  # 이미지 추가
async def add_job_post_image(  # 핸들러
    job_post_id: int,  # 공고 ID
    payload: JobPostImageCreate,  # 요청 바디
    user: User = Depends(require_role(UserRole.COMPANY)),  # 회사만
    db: AsyncSession = Depends(get_async_db),  # DB 세션
):
    job = await db.get(JobPost, job_post_id)  # 공고 조회

    if not job or job.is_deleted:  # 없거나 삭제됨
        raise HTTPException(status_code=404, detail="Job post not found")  # 404

    if job.company_id != user.id:  # 소유자 확인
        raise HTTPException(status_code=403, detail="Not your job post")  # 권한 오류

    img = JobPostImage(  # 이미지 생성
        job_post_id=job_post_id,  # 공고 ID
        image_url=payload.image_url,  # URL
    )
    db.add(img)  # 세션 추가
    await db.commit()  # 커밋
    await db.refresh(img)  # DB 반영

    return img  # 이미지 반환
