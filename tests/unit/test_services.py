"""
서비스 레이어 단위 테스트 - 간단한 버전
"""
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import _current_session
from app.db.base import Base
from app.models.taxonomy import Taxonomy, Term, TermVersion
from app.schemas.base import TermContentUpdate
from app.services.bootstrap_service import bootstrap_demo
from app.services.term_service import upsert_term_content

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


async def create_test_session():
    """테스트용 세션 생성"""
    engine = create_async_engine(TEST_DATABASE_URL)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return TestSessionLocal()


class TestBootstrapService:
    """Bootstrap 서비스 테스트"""

    @pytest.mark.asyncio
    async def test_bootstrap_demo_creates_data(self):
        """Bootstrap이 올바른 데이터를 생성하는지 테스트"""
        session = await create_test_session()

        try:
            await bootstrap_demo(session)
            await session.commit()

            # Check taxonomy
            taxonomies = (await session.execute(select(Taxonomy))).scalars().all()
            assert len(taxonomies) == 1
            assert taxonomies[0].taxonomy_code == "DATA_DOMAIN"

            # Check terms
            terms = (await session.execute(select(Term))).scalars().all()
            assert len(terms) == 2

            term_keys = [term.term_key for term in terms]
            assert "FIN" in term_keys
            assert "HR" in term_keys
        finally:
            await session.close()


class TestTermService:
    """Term 서비스 테스트"""

    @pytest.mark.asyncio
    async def test_upsert_term_content_new(self):
        """새로운 term content 생성 테스트"""
        session = await create_test_session()

        try:
            # Setup data
            await bootstrap_demo(session)
            await session.commit()

            # Get a term
            terms = (await session.execute(select(Term))).scalars().all()
            fin_term = next(term for term in terms if term.term_key == "FIN")

            content_update = TermContentUpdate(
                body_markdown="# Test Content",
                body_json={"test": "data"},
                author="test_user",
                reason="Initial creation"
            )

            # Set session context for @transactional decorator
            token = _current_session.set(session)
            try:
                version_id = await upsert_term_content(fin_term.term_id, content_update)
            finally:
                _current_session.reset(token)
                
            await session.commit()

            # Verify term was updated with current_version_id
            term = (await session.execute(
                select(Term).where(Term.term_id == fin_term.term_id)
            )).scalar_one()

            assert term.current_version_id == version_id

            # Verify version was created
            version = (await session.execute(
                select(TermVersion).where(TermVersion.version_id == version_id)
            )).scalar_one()

            assert version.body_markdown == "# Test Content"
            assert version.body_json == '{"test": "data"}'
            assert version.author == "test_user"
            assert version.change_reason == "Initial creation"
        finally:
            await session.close()

    @pytest.mark.asyncio
    async def test_upsert_term_content_update(self):
        """기존 term content 업데이트 테스트"""
        session = await create_test_session()

        try:
            # Setup data
            await bootstrap_demo(session)
            await session.commit()

            # Get a term
            terms = (await session.execute(select(Term))).scalars().all()
            hr_term = next(term for term in terms if term.term_key == "HR")

            # Create first version
            content_update_v1 = TermContentUpdate(
                body_markdown="# Version 1",
                author="user1"
            )

            # Set session context for @transactional decorator
            token = _current_session.set(session)
            try:
                version1_id = await upsert_term_content(hr_term.term_id, content_update_v1)
            finally:
                _current_session.reset(token)
            await session.commit()

            # Create second version
            content_update_v2 = TermContentUpdate(
                body_markdown="# Version 2",
                author="user2",
                reason="Updated content"
            )

            token = _current_session.set(session)
            try:
                version2_id = await upsert_term_content(hr_term.term_id, content_update_v2)
            finally:
                _current_session.reset(token)
            await session.commit()

            # Verify versions are different
            assert version1_id != version2_id

            # Verify term points to latest version
            term = (await session.execute(
                select(Term).where(Term.term_id == hr_term.term_id)
            )).scalar_one()

            assert term.current_version_id == version2_id

            # Verify old version is closed
            old_version = (await session.execute(
                select(TermVersion).where(TermVersion.version_id == version1_id)
            )).scalar_one()

            assert old_version.valid_to is not None  # Should be closed

            # Verify new version is open
            new_version = (await session.execute(
                select(TermVersion).where(TermVersion.version_id == version2_id)
            )).scalar_one()

            assert new_version.valid_to is None  # Should be open
        finally:
            await session.close()
