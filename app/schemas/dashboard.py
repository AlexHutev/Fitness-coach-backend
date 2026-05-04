"""Pydantic schemas for trainer dashboard summary data."""
from pydantic import BaseModel


class ActiveClientsStat(BaseModel):
    total: int
    delta_this_month: int


class ProgramsStat(BaseModel):
    total: int
    delta_this_week: int


class SessionsStat(BaseModel):
    total: int
    remaining: int


class ClientProgressStat(BaseModel):
    average_percentage: int  # rounded for display


class TrainerDashboardStats(BaseModel):
    active_clients: ActiveClientsStat
    programs: ProgramsStat
    sessions_this_week: SessionsStat
    client_progress: ClientProgressStat
