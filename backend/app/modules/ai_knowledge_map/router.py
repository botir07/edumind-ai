"""Knowledge Map API routes (/api/v1/ai/knowledge-map/*).

Builds the subject -> topic -> subtopic -> skill hierarchy and exposes
student mastery states computed transparently from real attempt data.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_core.access_control.dependencies import get_ai_enforcer
from app.ai_core.models.phase3_tables import (
    AIKnowledgeSubject,
    AIKnowledgeTopic,
    AIKnowledgeSubtopic,
)
from app.core.dependencies import get_current_user, require_role
from app.database.session import get_db
from app.models import Student

from .schemas import (
    KnowledgeMapOut,
    KnowledgeStateOut,
    KnowledgeSkillCreate,
    KnowledgeSkillOut,
    KnowledgeSubtopicCreate,
    KnowledgeSubtopicOut,
    KnowledgeSubjectCreate,
    KnowledgeSubjectOut,
    KnowledgeTopicCreate,
    KnowledgeTopicOut,
)
from .service import KnowledgeMapService

router = APIRouter(prefix="/ai/knowledge-map", tags=["ai_knowledge_map"])


def _build_service(db: AsyncSession, enforcer) -> KnowledgeMapService:
    return KnowledgeMapService(session=db, enforcer=enforcer)


async def _require_subject_org_access(
    db: AsyncSession, enforcer, subject_id: UUID
) -> AIKnowledgeSubject:
    subj = await db.get(AIKnowledgeSubject, subject_id)
    if not subj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    await enforcer.require_org_access(subj.organization_id)
    return subj


async def _require_topic_org_access(
    db: AsyncSession, enforcer, topic_id: UUID
) -> AIKnowledgeTopic:
    top = await db.get(AIKnowledgeTopic, topic_id)
    if not top:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    subj = await db.get(AIKnowledgeSubject, top.subject_id)
    await enforcer.require_org_access(subj.organization_id)
    return top


async def _require_subtopic_org_access(
    db: AsyncSession, enforcer, subtopic_id: UUID
):
    from app.ai_core.models.phase3_tables import AIKnowledgeSubtopic
    sub = await db.get(AIKnowledgeSubtopic, subtopic_id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subtopic not found")
    top = await db.get(AIKnowledgeTopic, sub.topic_id)
    subj = await db.get(AIKnowledgeSubject, top.subject_id)
    await enforcer.require_org_access(subj.organization_id)
    return sub


# ---------- Hierarchy (admin/teacher) ----------

@router.post("/subjects", response_model=KnowledgeSubjectOut, status_code=status.HTTP_201_CREATED)
async def create_subject(
    payload: KnowledgeSubjectCreate,
    current_user: dict = Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN", "TEACHER")),
    db: AsyncSession = Depends(get_db),
    enforcer=Depends(get_ai_enforcer),
):
    await enforcer.require_org_access(payload.organization_id)
    service = KnowledgeMapService(session=db, enforcer=enforcer)
    obj = await service.create_subject(
        organization_id=payload.organization_id, name=payload.name, code=payload.code
    )
    return KnowledgeSubjectOut.model_validate(obj)


@router.get("/subjects", response_model=List[KnowledgeSubjectOut])
async def list_subjects(
    organization_id: UUID = Query(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    enforcer=Depends(get_ai_enforcer),
):
    await enforcer.require_org_access(organization_id)
    service = KnowledgeMapService(session=db, enforcer=enforcer)
    return [KnowledgeSubjectOut.model_validate(s) for s in await service.list_subjects(organization_id)]


@router.post("/topics", response_model=KnowledgeTopicOut, status_code=status.HTTP_201_CREATED)
async def create_topic(
    payload: KnowledgeTopicCreate,
    current_user: dict = Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN", "TEACHER")),
    db: AsyncSession = Depends(get_db),
    enforcer=Depends(get_ai_enforcer),
):
    await _require_subject_org_access(db, enforcer, payload.subject_id)
    service = KnowledgeMapService(session=db, enforcer=enforcer)
    obj = await service.create_topic(
        subject_id=payload.subject_id, name=payload.name, code=payload.code, order_index=payload.order_index
    )
    return KnowledgeTopicOut.model_validate(obj)


@router.get("/topics", response_model=List[KnowledgeTopicOut])
async def list_topics(
    subject_id: UUID = Query(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    enforcer=Depends(get_ai_enforcer),
):
    await _require_subject_org_access(db, enforcer, subject_id)
    service = KnowledgeMapService(session=db, enforcer=enforcer)
    return [KnowledgeTopicOut.model_validate(t) for t in await service.list_topics(subject_id)]


@router.post("/subtopics", response_model=KnowledgeSubtopicOut, status_code=status.HTTP_201_CREATED)
async def create_subtopic(
    payload: KnowledgeSubtopicCreate,
    current_user: dict = Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN", "TEACHER")),
    db: AsyncSession = Depends(get_db),
    enforcer=Depends(get_ai_enforcer),
):
    await _require_topic_org_access(db, enforcer, payload.topic_id)
    service = KnowledgeMapService(session=db, enforcer=enforcer)
    obj = await service.create_subtopic(
        topic_id=payload.topic_id, name=payload.name, code=payload.code, order_index=payload.order_index
    )
    return KnowledgeSubtopicOut.model_validate(obj)


@router.get("/subtopics", response_model=List[KnowledgeSubtopicOut])
async def list_subtopics(
    topic_id: UUID = Query(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    enforcer=Depends(get_ai_enforcer),
):
    await _require_topic_org_access(db, enforcer, topic_id)
    service = KnowledgeMapService(session=db, enforcer=enforcer)
    return [KnowledgeSubtopicOut.model_validate(st) for st in await service.list_subtopics(topic_id)]


@router.post("/skills", response_model=KnowledgeSkillOut, status_code=status.HTTP_201_CREATED)
async def create_skill(
    payload: KnowledgeSkillCreate,
    current_user: dict = Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN", "TEACHER")),
    db: AsyncSession = Depends(get_db),
    enforcer=Depends(get_ai_enforcer),
):
    from app.ai_core.models.phase3_tables import AIKnowledgeSubtopic, AIKnowledgeTopic, AIKnowledgeSubject
    sub = await db.get(AIKnowledgeSubtopic, payload.subtopic_id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subtopic not found")
    top = await db.get(AIKnowledgeTopic, sub.topic_id)
    subj = await db.get(AIKnowledgeSubject, top.subject_id)
    await enforcer.require_org_access(subj.organization_id)
    service = KnowledgeMapService(session=db, enforcer=enforcer)
    obj = await service.create_skill(
        subtopic_id=payload.subtopic_id, name=payload.name, code=payload.code, order_index=payload.order_index
    )
    return KnowledgeSkillOut.model_validate(obj)


@router.get("/skills", response_model=List[KnowledgeSkillOut])
async def list_skills(
    subtopic_id: UUID = Query(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    enforcer=Depends(get_ai_enforcer),
):
    from app.ai_core.models.phase3_tables import AIKnowledgeSubtopic, AIKnowledgeTopic, AIKnowledgeSubject
    sub = await db.get(AIKnowledgeSubtopic, subtopic_id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subtopic not found")
    top = await db.get(AIKnowledgeTopic, sub.topic_id)
    subj = await db.get(AIKnowledgeSubject, top.subject_id)
    await enforcer.require_org_access(subj.organization_id)
    service = KnowledgeMapService(session=db, enforcer=enforcer)
    return [KnowledgeSkillOut.model_validate(k) for k in await service.list_skills(subtopic_id)]


@router.get("/mastery-algorithm", response_model=dict)
async def mastery_algorithm():
    """Return documentation of the transparent mastery algorithm (public)."""
    service = KnowledgeMapService(session=None, enforcer=None)  # type: ignore[arg-type]
    return service.mastery_algorithm_docs()


# ---------- Mastery map (student/teacher/parent/school-admin) ----------

@router.get("/{student_id}", response_model=KnowledgeMapOut)
async def get_knowledge_map(
    student_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    enforcer=Depends(get_ai_enforcer),
):
    """Get the full knowledge map for a student (role-scoped)."""
    result = await db.execute(
        __import__("sqlalchemy").select(Student).where(Student.id == student_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    organization_id = student.organization_id
    await enforcer.require_org_access(organization_id)

    service = KnowledgeMapService(session=db, enforcer=enforcer)
    data = await service.build_knowledge_map(student_id=student_id, organization_id=organization_id)
    return KnowledgeMapOut(
        subjects=[KnowledgeSubjectOut.model_validate(s) for s in data["subjects"]],
        topics=[KnowledgeTopicOut.model_validate(t) for t in data["topics"]],
        subtopics=[KnowledgeSubtopicOut.model_validate(st) for st in data["subtopics"]],
        skills=[KnowledgeSkillOut.model_validate(k) for k in data["skills"]],
        mastery_states=[KnowledgeStateOut.model_validate(m) for m in data["mastery_states"]],
    )
