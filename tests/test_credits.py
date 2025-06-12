from crunevo.utils.credits import add_credit, spend_credit
from crunevo.constants import CreditReasons
import pytest


def test_add_credit(db_session, test_user):
    old_balance = test_user.credits
    add_credit(test_user, 5, CreditReasons.APUNTE_SUBIDO)
    assert test_user.credits == old_balance + 5
    last = test_user.credit_history[-1]
    assert last.amount == 5
    assert last.reason == CreditReasons.APUNTE_SUBIDO


def test_spend_credit(db_session, test_user):
    add_credit(test_user, 3, CreditReasons.DONACION)
    spend_credit(test_user, 2, CreditReasons.COMPRA)
    assert test_user.credits == 1
    last = test_user.credit_history[-1]
    assert last.amount == -2
    assert last.reason == CreditReasons.COMPRA


def test_spend_insufficient(db_session, test_user):
    with pytest.raises(ValueError):
        spend_credit(test_user, 1, CreditReasons.COMPRA)
