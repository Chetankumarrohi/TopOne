from sqlalchemy.orm import Session

from app.identity.models.risk_answer import RiskAnswer


def create_many(
    db: Session,
    answers: list[RiskAnswer],
):
    db.add_all(answers)
    db.commit()

    return answers


def delete_by_profile(
    db: Session,
    risk_profile_id: int,
):
    (
        db.query(RiskAnswer)
        .filter(
            RiskAnswer.risk_profile_id
            == risk_profile_id
        )
        .delete(
            synchronize_session=False
        )
    )

    db.commit()


def get_by_profile(
    db: Session,
    risk_profile_id: int,
):
    return (
        db.query(RiskAnswer)
        .filter(
            RiskAnswer.risk_profile_id
            == risk_profile_id
        )
        .all()
    )