from pydantic import BaseModel, ConfigDict, Field


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GetLeaveBalanceArgs(StrictBaseModel):
    employee_id: int = Field(gt=0)


class GetTeamLeaveSummaryArgs(StrictBaseModel):
    pass


class GetEmployeeLeaveDetailsArgs(StrictBaseModel):
    employee_id: int = Field(gt=0)


class GetLowLeaveAlertsArgs(StrictBaseModel):
    threshold: int = Field(default=3, ge=0, le=30)


class GetLeaveLeaderboardArgs(StrictBaseModel):
    limit: int = Field(default=5, ge=1, le=50)


class ListEmployeesArgs(StrictBaseModel):
    limit: int = Field(default=20, ge=1, le=200)


class SearchEmployeesArgs(StrictBaseModel):
    query: str = Field(min_length=1, max_length=100)
    limit: int = Field(default=20, ge=1, le=100)


class GetRoleBreakdownArgs(StrictBaseModel):
    pass


class GetManagerLeaveDashboardArgs(StrictBaseModel):
    alert_threshold: int = Field(default=3, ge=0, le=30)
    leaderboard_limit: int = Field(default=5, ge=1, le=50)
