"""Development seed data for EduMind AI.

Creates clearly identified development accounts and fictional student information.
INTENDED FOR DEVELOPMENT AND TESTING ONLY - NOT FOR PRODUCTION.

Run:   python scripts/seed_dev.py   (from backend/ directory)
Requires: DATABASE_URL pointing to a (test) PostgreSQL/SQLite database.
"""
import asyncio
from datetime import date
from uuid import uuid4

from app.core.security import get_password_hash
from app.database.session import AsyncSessionLocal, engine
from app.database.base import Base
import app.models  # noqa: F401

DEV_PASSWORD = "DevPassword123!"


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        from app.models.academic_year import AcademicYear
        from app.models.class_ import Class
        from app.models.class_enrollment import ClassEnrollment
        from app.models.class_subject import ClassSubject
        from app.models.grade_level import GradeLevel
        from app.models.organization import Organization
        from app.models.organization_membership import OrganizationMembership
        from app.models.student import Student
        from app.models.student_guardian import StudentGuardian
        from app.models.subject import Subject
        from app.models.teacher import Teacher
        from app.models.user import User

        # ---- Super admin ----
        su = User(
            email="admin@edumind.uz",
            hashed_password=get_password_hash("SuperAdmin123!"),
            full_name="Super Admin",
            is_active=True,
            is_superuser=True,
            locale="uz",
        )
        session.add(su)
        await session.flush()

        # ---- School ----
        org = Organization(
            name="Tashkent International School",
            code="TASH01",
            legal_name="MMC Tashkent International School LLC",
            address="1 Navoi Street, Tashkent, Uzbekistan",
            phone="+998 71 123-45-67",
            email="info@tashschool.uz",
            timezone="Asia/Tashkent",
            is_active=True,
        )
        session.add(org)
        await session.flush()

        # School admin
        sa = User(
            email="schooladmin@tashschool.uz",
            hashed_password=get_password_hash(DEV_PASSWORD),
            full_name="School Administrator",
            is_active=True,
            locale="uz",
        )
        session.add(sa)
        await session.flush()
        session.add(OrganizationMembership(user_id=sa.id, organization_id=org.id, role="SCHOOL_ADMIN", is_active=True))

        # Teacher
        tu = User(
            email="teacher@tashschool.uz",
            hashed_password=get_password_hash(DEV_PASSWORD),
            full_name="Ozoda Karimova",
            is_active=True,
            locale="uz",
        )
        session.add(tu)
        await session.flush()
        teacher = Teacher(
            user_id=tu.id,
            organization_id=org.id,
            employee_number="EMP-001",
            subject_specialization="Mathematics",
            hire_date=date(2018, 9, 1),
            status="active",
        )
        session.add(teacher)
        await session.flush()
        session.add(OrganizationMembership(user_id=tu.id, organization_id=org.id, role="TEACHER", is_active=True))

        # Student
        stu = User(
            email="student@tashschool.uz",
            hashed_password=get_password_hash(DEV_PASSWORD),
            full_name="Aliyor Rahimov",
            is_active=True,
            locale="uz",
        )
        session.add(stu)
        await session.flush()
        student = Student(
            user_id=stu.id,
            organization_id=org.id,
            student_number="STU-001",
            date_of_birth=date(2012, 5, 10),
            gender="male",
            address="123 Chilonzor, Tashkent",
            status="active",
        )
        session.add(student)
        await session.flush()

        # Parent
        par = User(
            email="parent@tashschool.uz",
            hashed_password=get_password_hash(DEV_PASSWORD),
            full_name="Dilnoza Rahimova",
            is_active=True,
            locale="uz",
        )
        session.add(par)
        await session.flush()
        # Parent profile
        from app.models.parent import Parent
        parent = Parent(user_id=par.id, organization_id=org.id)
        session.add(parent)
        await session.flush()

        # Academic structure
        year = AcademicYear(
            organization_id=org.id,
            name="2026-2027",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 6, 30),
            is_current=True,
        )
        session.add(year)
        await session.flush()
        grade = GradeLevel(organization_id=org.id, name="5", level_order=5)
        session.add(grade)
        await session.flush()
        klass = Class(organization_id=org.id, grade_id=grade.id, name="5-A")
        session.add(klass)
        await session.flush()
        subject = Subject(organization_id=org.id, name="Mathematics", code="MATH")
        session.add(subject)
        await session.flush()
        class_subject = ClassSubject(
            class_id=klass.id,
            subject_id=subject.id,
            teacher_id=teacher.id,
            academic_year_id=year.id,
        )
        session.add(class_subject)
        await session.flush()
        session.add(
            ClassEnrollment(
                student_id=student.id,
                class_id=klass.id,
                academic_year_id=year.id,
                enrolled_at=date(2026, 9, 1),
                status="active",
            )
        )
        # Guardian relationship (verified)
        session.add(
            StudentGuardian(
                student_id=student.id,
                parent_id=parent.id,
                relationship="mother",
                is_verified=True,
                verified_by=sa.id,
            )
        )

        await session.commit()
        print("Seed data created.")
        print("Dev accounts (password DevPassword123!):")
        print("  admin@edumind.uz          (SUPER_ADMIN)")
        print("  schooladmin@tashschool.uz (SCHOOL_ADMIN)")
        print("  teacher@tashschool.uz     (TEACHER)")
        print("  student@tashschool.uz     (STUDENT)")
        print("  parent@tashschool.uz      (PARENT)")


if __name__ == "__main__":
    asyncio.run(main())
