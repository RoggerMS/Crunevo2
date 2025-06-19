from __future__ import annotations

from datetime import datetime, timedelta, date
from collections import OrderedDict
from sqlalchemy import func

from crunevo.extensions import db
from crunevo.models import EmailToken, Note, Credit, Product


def _fill_series(start: date, periods: int, step: timedelta, rows):
    data = OrderedDict(
        ((start + step * i).strftime("%Y-%m-%d"), 0) for i in range(periods)
    )
    for dt, count in rows:
        key = dt.strftime("%Y-%m-%d")
        data[key] = int(count)
    labels = list(data.keys())
    values = list(data.values())
    return labels, values


def user_registrations_last_7_days():
    today = datetime.utcnow().date()
    start = today - timedelta(days=6)
    rows = (
        db.session.query(func.date(EmailToken.created_at), func.count())
        .filter(EmailToken.created_at >= start)
        .group_by(func.date(EmailToken.created_at))
        .order_by(func.date(EmailToken.created_at))
        .all()
    )
    labels, values = _fill_series(start, 7, timedelta(days=1), rows)
    return {"label": "Usuarios", "labels": labels, "values": values}


def notes_last_4_weeks():
    today = datetime.utcnow().date()
    start = today - timedelta(weeks=3)
    start -= timedelta(days=start.weekday())
    rows = (
        db.session.query(func.date_trunc("week", Note.created_at), func.count())
        .filter(Note.created_at >= start)
        .group_by(func.date_trunc("week", Note.created_at))
        .order_by(func.date_trunc("week", Note.created_at))
        .all()
    )
    labels, values = _fill_series(start, 4, timedelta(weeks=1), rows)
    return {"label": "Apuntes", "labels": labels, "values": values}


def credits_last_4_weeks():
    today = datetime.utcnow().date()
    start = today - timedelta(weeks=3)
    start -= timedelta(days=start.weekday())
    rows = (
        db.session.query(
            func.date_trunc("week", Credit.timestamp), func.sum(Credit.amount)
        )
        .filter(Credit.timestamp >= start)
        .group_by(func.date_trunc("week", Credit.timestamp))
        .order_by(func.date_trunc("week", Credit.timestamp))
        .all()
    )
    labels, values = _fill_series(start, 4, timedelta(weeks=1), rows)
    values = [float(v) for v in values]
    return {"label": "Créditos", "labels": labels, "values": values}


def _month_add(dt: date, months: int) -> date:
    year = dt.year + (dt.month - 1 + months) // 12
    month = (dt.month - 1 + months) % 12 + 1
    return date(year, month, 1)


def products_last_3_months():
    today = datetime.utcnow().date()
    first = date(today.year, today.month, 1)
    start = _month_add(first, -2)
    if hasattr(Product, "created_at"):
        rows = (
            db.session.query(func.date_trunc("month", Product.created_at), func.count())
            .filter(Product.created_at >= start)
            .group_by(func.date_trunc("month", Product.created_at))
            .order_by(func.date_trunc("month", Product.created_at))
            .all()
        )
    else:
        rows = []
    # Ajuste de etiquetas y valores para el gráfico mensual
    labels = [_month_add(start, i).strftime("%Y-%m") for i in range(3)]
    mapping = {dt.strftime("%Y-%m"): int(count) for dt, count in rows}
    values = [mapping.get(label, 0) for label in labels]
    return {"label": "Productos", "labels": labels, "values": values}
