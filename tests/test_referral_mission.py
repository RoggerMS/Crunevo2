from crunevo.models import Mission, Referral
from crunevo.routes.missions_routes import compute_mission_states


def test_referral_progress(db_session, test_user, another_user):
    mission = Mission(
        code="referido_1",
        description="Invita a 1",
        goal=1,
        credit_reward=10,
    )
    db_session.add(mission)
    referral = Referral(
        code="code",
        invitador_id=test_user.id,
        invitado_id=another_user.id,
        completado=True,
    )
    db_session.add(referral)
    db_session.commit()

    progress = compute_mission_states(test_user)[mission.id]
    assert progress["progreso"] == 1
    assert progress["completada"] is True
