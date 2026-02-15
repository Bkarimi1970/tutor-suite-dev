from core.schema import TutorRequest, TutorResponse
from math_tutor import run_tutor_turn


def handle_request(req: TutorRequest) -> TutorResponse:
    """
    Central orchestration layer.
    Routes structured request into tutor system.
    """

    # Decide what message to send
    if req.mode == "solve":
        message = req.problem
    else:
        message = req.student_step or req.problem

    data = run_tutor_turn(
        user_id=req.user_id,
        level=req.level,
        mode=req.mode,
        student_message=message,
    )

    return TutorResponse(**data)
