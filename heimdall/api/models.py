from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Action(BaseModel):
    model_config = ConfigDict(extra='forbid')
    idempotency_key: str = Field(min_length=1, max_length=128)
    kind: Literal['read', 'email', 'quote', 'terms', 'invoice', 'order', 'upload', 'delete', 'news']
    sources: list[str] = Field(min_length=1, max_length=20)
    text: str = Field(default='', max_length=10000)
    scope: Literal['declared', 'outside'] = 'declared'
    recipient: Literal['known', 'unknown'] = 'unknown'
    amount: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    list_price: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    customer: str = Field(default='', max_length=100)
    retaining: bool = False
    destination: Literal['external', 'local'] = 'external'
    invoice_matches: bool = False
    written_confirmation: bool = False
    changed_terms: bool = False
    contract_directed_error: bool = False
    announced: bool = False

    @model_validator(mode='after')
    def required_prices(self):
        if self.kind == 'quote' and (self.amount is None or self.list_price is None):
            raise ValueError('quote requires amount and list_price')
        return self


class Approval(BaseModel):
    model_config = ConfigDict(extra='forbid')
    decision: Literal['approve', 'deny']
    owner_note: str = Field(min_length=1, max_length=2000)
