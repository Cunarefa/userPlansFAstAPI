from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class ClosedCreditInfo(BaseModel):
    return_date: date
    body: int
    percent: Decimal
    total_paid: Decimal

class OpenCreditInfo(BaseModel):
    return_date: date
    days_overdue: int
    body: int
    percent: Decimal
    body_paid: Decimal
    percent_paid: Decimal

class CreditOutput(BaseModel):
    id: int
    issuance_date: date
    is_closed: bool
    closed_info: ClosedCreditInfo | None = None
    open_info: OpenCreditInfo | None = None

    class Config:
        from_attributes = True


class PlansPerformanceSchema(BaseModel):
    plan_month: str
    category_id: int
    sum: int
    total: int
    plan_fulfillment_percentage: int
