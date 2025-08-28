from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.user_plans_app.models import Payment, Credit
from app.user_plans_app.schemas import CreditOutput, ClosedCreditInfo, OpenCreditInfo

router = APIRouter(prefix="/user_credits", tags=["User Credits"])


@router.get("/{user_id}", response_model=list[CreditOutput])
async def get_user_credits(user_id: int, session: AsyncSession = Depends(get_session)):
    # Get User's credits
    stmt = select(Credit).where(Credit.user_id == user_id)
    result = await session.execute(stmt)
    user_credits = result.scalars().all()

    # Get Payment's sums
    credit_ids = [c.id for c in user_credits]
    stmt_payments = (
        select(
            Payment.credit_id,
            func.sum(case((Payment.type_id == 1, Payment.sum), else_=0)).label("body_paid"),
            func.sum(case((Payment.type_id == 2, Payment.sum), else_=0)).label("percent_paid"),
            func.sum(Payment.sum).label("total_paid")
        )
        .where(Payment.credit_id.in_(credit_ids))
        .group_by(Payment.credit_id)
    )

    payments_result = await session.execute(stmt_payments)
    payments_summary = {r.credit_id: r for r in payments_result}

    output = []
    for credit in user_credits:
        payments = payments_summary.get(credit.id)
        is_closed = credit.actual_return_date is not None

        if is_closed:
            closed_info = ClosedCreditInfo(
                return_date=credit.actual_return_date,
                body=credit.body,
                percent=credit.percent,
                total_paid=payments.total_paid if payments else 0
            )
            open_info = None
        else:
            open_info = OpenCreditInfo(
                return_date=credit.return_date,
                days_overdue=max((date.today() - credit.return_date).days, 0),
                body=credit.body,
                percent=credit.percent,
                body_paid=payments.body_paid if payments else 0,
                percent_paid=payments.percent_paid if payments else 0,
            )
            closed_info = None

        output.append(
            CreditOutput(
                id=credit.id,
                issuance_date=credit.issuance_date,
                is_closed=is_closed,
                closed_info=closed_info,
                open_info=open_info
            )
        )
    return output


