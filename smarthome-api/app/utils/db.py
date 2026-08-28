"""数据库查询常用辅助。

集中「执行查询、结果为空则抛 HTTP 异常」的样板，避免 Device / Room / Scene
等服务的 ``*_or_404`` 辅助函数各自重复这段逻辑。
"""
from fastapi import HTTPException, status
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session


def get_or_404(
    db: Session,
    statement: Select,
    *,
    detail: str = "资源不存在",
    status_code: int = status.HTTP_404_NOT_FOUND,
):
    """执行查询，结果为空时抛出 HTTP 异常。

    ``statement`` 直接传入 ``select(Model).where(...)`` 之类的可执行语句。
    """
    obj = db.scalar(statement)
    if obj is None:
        raise HTTPException(status_code=status_code, detail=detail)
    return obj


def count_query(db: Session, statement: Select) -> int:
    """对已有查询计数（包装为子查询后再 count）。"""
    return db.scalar(select(func.count()).select_from(statement.subquery())) or 0


def paginate(db: Session, statement: Select, *, page: int = 1, page_size: int = 20):
    """对查询分页，返回 ``(items, total)``。

    ``page`` 从 1 开始；``offset`` 由 ``(page - 1) * page_size`` 计算。
    """
    total = count_query(db, statement)
    items = db.scalars(
        statement.offset((page - 1) * page_size).limit(page_size)
    ).all()
    return items, total
