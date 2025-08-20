from datetime import datetime, timedelta, timezone

from crunevo.utils.helpers import timesince


def test_timesince_handles_timezone_awareness():
    tz = timezone(timedelta(hours=5))
    dt = datetime.now(tz) - timedelta(hours=1)
    assert timesince(dt) == "hace 1 hora"
