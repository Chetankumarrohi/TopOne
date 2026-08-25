from sqlalchemy.orm import Session

from app.identity.models.risk_profile import RiskProfile
from app.identity.models.risk_answer import RiskAnswer
from app.identity.models.financial_profile import FinancialProfile

from app.identity.repositories.risk_repository import (
    get_by_user,
)

from app.identity.risk_questionnaire import (
    RISK_QUESTIONS,
    RISK_QUESTIONNAIRE_VERSION,
)


# ---------------------------------------------------------
# Questionnaire
# ---------------------------------------------------------

def get_risk_questions():
    """
    Returns questionnaire without exposing internal scores.
    """

    questions = []

    for question in RISK_QUESTIONS:
        questions.append(
            {
                "code": question["code"],
                "question": question["question"],
                "dimension": question["dimension"],
                "options": [
                    {
                        "value": option["value"],
                        "label": option["label"],
                    }
                    for option in question["options"]
                ],
            }
        )

    return questions


# ---------------------------------------------------------
# Questionnaire validation + scoring
# ---------------------------------------------------------

def score_questionnaire(answers):
    question_map = {
        question["code"]: question
        for question in RISK_QUESTIONS
    }

    required_codes = set(question_map.keys())

    submitted_codes = [
        answer.question_code
        for answer in answers
    ]

    # Prevent duplicate answers
    if len(submitted_codes) != len(set(submitted_codes)):
        raise ValueError(
            "Duplicate questionnaire answers are not allowed."
        )

    submitted_code_set = set(submitted_codes)

    missing = required_codes - submitted_code_set

    if missing:
        raise ValueError(
            "Please answer all risk assessment questions."
        )

    unknown = submitted_code_set - required_codes

    if unknown:
        raise ValueError(
            f"Invalid risk question: {next(iter(unknown))}"
        )

    scored_answers = []

    dimension_scores = {
        "behaviour": [],
        "horizon": [],
        "experience": [],
        "liquidity": [],
    }

    for answer in answers:
        question = question_map[answer.question_code]

        option = next(
            (
                item
                for item in question["options"]
                if item["value"] == answer.answer_value
            ),
            None,
        )

        if not option:
            raise ValueError(
                f"Invalid answer for {answer.question_code}."
            )

        score = float(option["score"])
        dimension = question["dimension"]

        dimension_scores[dimension].append(score)

        scored_answers.append(
            {
                "question_code": answer.question_code,
                "answer_value": answer.answer_value,
                "score_awarded": score,
            }
        )

    def average(values):
        if not values:
            return 0.0

        return sum(values) / len(values)

    return {
        "answers": scored_answers,
        "behaviour_score": average(
            dimension_scores["behaviour"]
        ),
        "horizon_score": average(
            dimension_scores["horizon"]
        ),
        "experience_score": average(
            dimension_scores["experience"]
        ),
        "liquidity_score": average(
            dimension_scores["liquidity"]
        ),
    }


# ---------------------------------------------------------
# Financial risk capacity
# ---------------------------------------------------------

def calculate_capacity_score(
    financial_profile: FinancialProfile,
) -> float:

    score = 0.0

    # --------------------------------
    # Savings rate — max 30 points
    # --------------------------------

    savings_rate = financial_profile.savings_rate

    if savings_rate >= 30:
        score += 30
    elif savings_rate >= 20:
        score += 24
    elif savings_rate >= 10:
        score += 16
    elif savings_rate > 0:
        score += 8

    # --------------------------------
    # Debt-to-income — max 25 points
    # Lower debt = more capacity
    # --------------------------------

    debt_ratio = financial_profile.debt_to_income_ratio

    if debt_ratio <= 10:
        score += 25
    elif debt_ratio <= 20:
        score += 20
    elif debt_ratio <= 30:
        score += 14
    elif debt_ratio <= 40:
        score += 7

    # --------------------------------
    # Emergency fund — max 25 points
    # --------------------------------

    emergency_months = financial_profile.emergency_months

    if emergency_months >= 6:
        score += 25
    elif emergency_months >= 3:
        score += 17
    elif emergency_months >= 1:
        score += 8

    # --------------------------------
    # Net worth — max 10 points
    # --------------------------------

    if financial_profile.net_worth > 0:
        score += 10

    # --------------------------------
    # Insurance protection — max 10
    # --------------------------------

    if financial_profile.insurance_cover > 0:
        score += 10

    return min(round(score, 2), 100.0)


# ---------------------------------------------------------
# Final score
# ---------------------------------------------------------

def calculate_final_score(
    capacity_score: float,
    behaviour_score: float,
    horizon_score: float,
    experience_score: float,
    liquidity_score: float,
) -> float:

    final_score = (
        capacity_score * 0.30
        + behaviour_score * 0.30
        + horizon_score * 0.20
        + experience_score * 0.10
        + liquidity_score * 0.10
    )

    return round(final_score, 2)


# ---------------------------------------------------------
# Classification
# ---------------------------------------------------------

def classify_risk(score: float):

    if score < 40:
        return {
            "category": "Conservative",
            "equity_min": 10.0,
            "equity_max": 35.0,
        }

    if score < 70:
        return {
            "category": "Moderate",
            "equity_min": 35.0,
            "equity_max": 65.0,
        }

    return {
        "category": "Aggressive",
        "equity_min": 65.0,
        "equity_max": 85.0,
    }


# ---------------------------------------------------------
# Internal profile builder
# ---------------------------------------------------------

def build_risk_profile(
    db: Session,
    user_id: int,
    data,
    existing_profile=None,
):

    financial_profile = (
        db.query(FinancialProfile)
        .filter(
            FinancialProfile.user_id == user_id
        )
        .first()
    )

    if not financial_profile:
        raise ValueError(
            "Complete your financial profile before "
            "taking the risk assessment."
        )

    questionnaire = score_questionnaire(
        data.answers
    )

    capacity_score = calculate_capacity_score(
        financial_profile
    )

    final_score = calculate_final_score(
        capacity_score=capacity_score,
        behaviour_score=questionnaire[
            "behaviour_score"
        ],
        horizon_score=questionnaire[
            "horizon_score"
        ],
        experience_score=questionnaire[
            "experience_score"
        ],
        liquidity_score=questionnaire[
            "liquidity_score"
        ],
    )

    classification = classify_risk(
        final_score
    )

    if existing_profile:
        profile = existing_profile

        # Remove previous questionnaire answers
        profile.answers.clear()

    else:
        profile = RiskProfile(
            user_id=user_id
        )

        db.add(profile)

    profile.capacity_score = capacity_score

    profile.behaviour_score = round(
        questionnaire["behaviour_score"],
        2,
    )

    profile.horizon_score = round(
        questionnaire["horizon_score"],
        2,
    )

    profile.experience_score = round(
        questionnaire["experience_score"],
        2,
    )

    profile.liquidity_score = round(
        questionnaire["liquidity_score"],
        2,
    )

    profile.final_risk_score = final_score

    profile.risk_category = (
        classification["category"]
    )

    profile.recommended_equity_min = (
        classification["equity_min"]
    )

    profile.recommended_equity_max = (
        classification["equity_max"]
    )

    profile.scoring_version = (
        RISK_QUESTIONNAIRE_VERSION
    )

    # Flush first so a new profile gets an ID
    db.flush()

    for answer in questionnaire["answers"]:

        risk_answer = RiskAnswer(
            risk_profile_id=profile.id,
            question_code=answer[
                "question_code"
            ],
            answer_value=answer[
                "answer_value"
            ],
            score_awarded=answer[
                "score_awarded"
            ],
        )

        db.add(risk_answer)

    db.commit()
    db.refresh(profile)

    return profile


# ---------------------------------------------------------
# Create assessment
# ---------------------------------------------------------

def create_risk_profile(
    db: Session,
    user_id: int,
    data,
):

    existing = get_by_user(
        db,
        user_id,
    )

    if existing:
        raise ValueError(
            "Risk assessment already exists. "
            "Use reassessment to update it."
        )

    return build_risk_profile(
        db=db,
        user_id=user_id,
        data=data,
    )


# ---------------------------------------------------------
# Get profile
# ---------------------------------------------------------

def get_risk_profile(
    db: Session,
    user_id: int,
):

    profile = get_by_user(
        db,
        user_id,
    )

    if not profile:
        raise ValueError(
            "Risk profile not found."
        )

    return profile


# ---------------------------------------------------------
# Reassessment / Update
# ---------------------------------------------------------

def update_risk_profile(
    db: Session,
    user_id: int,
    data,
):

    profile = get_by_user(
        db,
        user_id,
    )

    if not profile:
        raise ValueError(
            "Risk profile not found."
        )

    return build_risk_profile(
        db=db,
        user_id=user_id,
        data=data,
        existing_profile=profile,
    )