from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.models.codeset import Code, CodeSet, CodeVersion
from app.schemas.base import CodeCreate, CodeOut, CodeSetCreate, CodeSetOut

router = APIRouter(prefix="/codeset", tags=["codeset"])


@router.get("/", response_model=list[CodeSetOut])
async def list_codesets(session: AsyncSession = Depends(get_session)):
    """Get all codesets"""
    result = await session.execute(select(CodeSet).order_by(CodeSet.name))
    codesets = result.scalars().all()
    return [CodeSetOut(
        codeset_id=cs.codeset_id,
        codeset_code=cs.codeset_code,
        name=cs.name,
        description=cs.description,
        created_at=cs.created_at
    ) for cs in codesets]


@router.get("/{codeset_code}", response_model=CodeSetOut)
async def get_codeset(codeset_code: str, session: AsyncSession = Depends(get_session)):
    """Get a specific codeset by code"""
    result = await session.execute(
        select(CodeSet).where(CodeSet.codeset_code == codeset_code)
    )
    codeset = result.scalar_one_or_none()
    if not codeset:
        raise HTTPException(404, "codeset not found")

    return CodeSetOut(
        codeset_id=codeset.codeset_id,
        codeset_code=codeset.codeset_code,
        name=codeset.name,
        description=codeset.description,
        created_at=codeset.created_at
    )


@router.post("/", response_model=CodeSetOut)
async def create_codeset(data: CodeSetCreate, session: AsyncSession = Depends(get_session)):
    """Create a new codeset"""
    # Check if codeset_code already exists
    existing = await session.execute(
        select(CodeSet).where(CodeSet.codeset_code == data.codeset_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, f"codeset with code '{data.codeset_code}' already exists")

    codeset = CodeSet(
        codeset_code=data.codeset_code,
        name=data.name,
        description=data.description
    )
    session.add(codeset)
    await session.commit()
    await session.refresh(codeset)

    return CodeSetOut(
        codeset_id=codeset.codeset_id,
        codeset_code=codeset.codeset_code,
        name=codeset.name,
        description=codeset.description,
        created_at=codeset.created_at
    )


@router.get("/{codeset_code}/codes", response_model=list[CodeOut])
async def list_codes(codeset_code: str, session: AsyncSession = Depends(get_session)):
    """Get all codes in a codeset"""
    # First find the codeset
    codeset_result = await session.execute(
        select(CodeSet).where(CodeSet.codeset_code == codeset_code)
    )
    codeset = codeset_result.scalar_one_or_none()
    if not codeset:
        raise HTTPException(404, "codeset not found")

    # Get codes
    result = await session.execute(
        select(Code).where(Code.codeset_id == codeset.codeset_id).order_by(Code.code_key)
    )
    codes = result.scalars().all()

    return [CodeOut(
        code_id=code.code_id,
        code_key=code.code_key,
        codeset_id=code.codeset_id,
        current_version_id=code.current_version_id,
        created_at=code.created_at
    ) for code in codes]


@router.post("/{codeset_code}/codes", response_model=CodeOut)
async def create_code(
    codeset_code: str,
    data: CodeCreate,
    session: AsyncSession = Depends(get_session)
):
    """Create a new code in a codeset"""
    # Find the codeset
    codeset_result = await session.execute(
        select(CodeSet).where(CodeSet.codeset_code == codeset_code)
    )
    codeset = codeset_result.scalar_one_or_none()
    if not codeset:
        raise HTTPException(404, "codeset not found")

    # Check if code_key already exists in this codeset
    existing = await session.execute(
        select(Code).where(
            Code.codeset_id == codeset.codeset_id,
            Code.code_key == data.code_key
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, f"code with key '{data.code_key}' already exists in this codeset")

    # Create code
    code = Code(
        codeset_id=codeset.codeset_id,
        code_key=data.code_key
    )
    session.add(code)
    await session.flush()  # Get the code_id

    # Create initial version if label provided
    if data.label_default:
        version = CodeVersion(
            code_id=code.code_id,
            version_no=1,
            label_default=data.label_default
        )
        session.add(version)
        await session.flush()
        code.current_version_id = version.code_version_id

    await session.commit()
    await session.refresh(code)

    return CodeOut(
        code_id=code.code_id,
        code_key=code.code_key,
        codeset_id=code.codeset_id,
        current_version_id=code.current_version_id,
        created_at=code.created_at
    )
