from typing import Optional
from pydantic import BaseModel

class TimeModeRequest(BaseModel):
    mode: str  # 'REAL' or 'DEMO'

class SetTimeRequest(BaseModel):
    datetime: str  # ISO string or 'YYYY-MM-DD HH:MM:SS' or 'YYYY-MM-DDTHH:MM'

class AdvanceTimeRequest(BaseModel):
    minutes: int  # 1, 5, 30, 60, 360, 720, etc.

class SlotInfoResponse(BaseModel):
    mode: str
    timezone: str
    current_time: str
    date: str
    time_formatted: str
    slot_id: str
    slot_number: int
    slot_name: str
    slot_start: str
    slot_end: str
    slot_start_formatted: str
    slot_end_formatted: str
    remaining_seconds: int
    remaining_formatted: str
    next_slot_id: str
