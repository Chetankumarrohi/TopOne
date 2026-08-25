from typing import List

from pydantic import BaseModel, ConfigDict, Field


class RiskAnswerInput(BaseModel):
    question_code: str
    answer_value: str


class RiskAssessmentCreate(BaseModel):
    answers: List[RiskAnswerInput] = Field(
        min_length=1
    )


class RiskAssessmentUpdate(BaseModel):
    answers: List[RiskAnswerInput] = Field(
        min_length=1
    )


class RiskAnswerResponse(BaseModel):
    question_code: str
    answer_value: str
    score_awarded: float

    model_config = ConfigDict(
        from_attributes=True
    )


class RiskProfileResponse(BaseModel):
    id: int
    user_id: int

    capacity_score: float
    behaviour_score: float
    horizon_score: float
    experience_score: float
    liquidity_score: float

    final_risk_score: float
    risk_category: str

    recommended_equity_min: float
    recommended_equity_max: float

    scoring_version: str

    answers: List[RiskAnswerResponse]

    model_config = ConfigDict(
        from_attributes=True
    )


class RiskQuestionOption(BaseModel):
    value: str
    label: str


class RiskQuestionResponse(BaseModel):
    code: str
    question: str
    dimension: str
    options: List[RiskQuestionOption]