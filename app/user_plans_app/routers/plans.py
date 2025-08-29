import csv
from datetime import datetime, date
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select, func, case, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.user_plans_app.models import Plan, Dictionary, Credit, Payment
from app.user_plans_app.schemas import PlansPerformanceSchema

router = APIRouter(prefix="/plans", tags=["Plans"])


@router.post("/plans_insert", response_model=None)
async def insert_plan(file: UploadFile = File(), session: AsyncSession = Depends(get_session)):
    content = await file.read()
    decoded = content.decode("utf-8").splitlines()
    reader = csv.DictReader(decoded, delimiter=";")

    plans_to_add = []
    for idx, row in enumerate(reader, start=2):
        try:
            period = datetime.strptime(row["period"], "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Incorrect date format in row {idx}, {row}")

        if period.day != 1:
            raise HTTPException(status_code=400, detail=f"Should be the first day of the month, row {idx}")

        if row["sum"].strip() == "":
            raise HTTPException(status_code=400, detail=f"Sum cannot be empty, row {idx}")

        amount = float(row["sum"])
        category_id = int(row["category_id"])
        if period.month == 12:
            next_month = date(period.year + 1, 1, 1)
        else:
            next_month = date(period.year, period.month + 1, 1)

        existing = await session.execute(
            select(Plan).where(
                func.date_trunc("month", Plan.period) == next_month,
                Plan.category_id == category_id
            )
        )
        if existing.scalars().first():
            raise HTTPException(
                status_code=400, detail=f"Plan with period {period} and category {category_id} already exists."
            )

        plans_to_add.append(
            Plan(period=period, category_id=category_id, sum=amount)
        )

    for plan in plans_to_add:
        session.add(plan)
    await session.commit()

    return {"detail": "File successfully added."}

@router.get("/plans_performance", response_model=List[PlansPerformanceSchema])
async def get_plan_performance(check_date: str, session: AsyncSession = Depends(get_session)):
    try:
        period = datetime.strptime(check_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Plan date should be in format: YYYY-MM-DD")

    stmt = (
        select(
            Plan.period.label("plan_month"),
            Plan.category_id,
            func.sum(Plan.sum),
            (
                func.coalesce(
                    func.sum(
                        case(
                            (Plan.category_id == 3, Credit.body),
                            (Plan.category_id == 4, Payment.sum),
                            else_=0
                        )
                    ),
                    0
                )
            ).label("total"),
            (
                func.coalesce(
                    func.sum(
                        case(
                            (Plan.category_id == 3, Credit.body),
                            (Plan.category_id == 4, Payment.sum),
                            else_=0
                        )
                    ) * 100 / func.nullif(func.sum(Plan.sum), 0),
                    0
                )
            ).label("plan_fulfillment_percentage"),
        )
        .join(Dictionary, Dictionary.id == Plan.category_id)
        .outerjoin(
            Credit,
            and_(
                Plan.category_id == 3,
                extract("month", Credit.issuance_date) == extract("month", Plan.period),
                extract("year", Credit.issuance_date) == extract("year", Plan.period),
            ),
        )
        .outerjoin(
            Payment,
            and_(
                Plan.category_id == 4,
                Payment.type_id == Dictionary.id,
                extract("month", Payment.payment_date) == extract("month", Plan.period),
                extract("year", Payment.payment_date) == extract("year", Plan.period),
            ),
        )
        .where(Plan.period <= period)
        .group_by(Plan.period, Plan.category_id)
    )

    result = await session.execute(stmt)
    rows = result.all()

    output = [
        PlansPerformanceSchema(
            plan_month=str(row.plan_month),
            category_id=row.category_id,
            sum=row.sum,
            total=row.total,
            plan_fulfillment_percentage=int(row.plan_fulfillment_percentage or 0)
        )
        for row in rows
    ]

    return output
