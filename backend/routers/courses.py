"""Course management routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database import get_db
from models import Course, Hole, TeeSet, TeeHole
from schemas import CourseOut, CourseCreate, CourseSummary
from typing import List

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.post("/", response_model=CourseOut)
async def create_course(course: CourseCreate, db: AsyncSession = Depends(get_db)):
    db_course = Course(
        name=course.name,
        location=course.location,
        country=course.country,
        num_holes=course.num_holes,
        course_rating=course.course_rating,
        slope_rating=course.slope_rating,
    )
    db.add(db_course)
    await db.flush()

    for hole_data in course.holes:
        db_hole = Hole(
            course_id=db_course.id,
            hole_number=hole_data.hole_number,
            par=hole_data.par,
            stroke_index=hole_data.stroke_index,
            yards=hole_data.yards,
        )
        db.add(db_hole)

    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(Course)
        .options(selectinload(Course.holes), selectinload(Course.tee_sets).selectinload(TeeSet.tee_holes))
        .where(Course.id == db_course.id)
    )
    return result.scalar_one()


@router.get("/", response_model=List[CourseSummary])
async def list_courses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Course).order_by(Course.name))
    return result.scalars().all()


@router.get("/{course_id}", response_model=CourseOut)
async def get_course(course_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Course)
        .options(selectinload(Course.holes), selectinload(Course.tee_sets).selectinload(TeeSet.tee_holes))
        .where(Course.id == course_id)
    )
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.delete("/{course_id}")
async def delete_course(course_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    await db.delete(course)
    await db.commit()
    return {"ok": True}
