
from flask import Blueprint, render_template
from crunevo.models.event import Event

event_bp = Blueprint('event', __name__)


@event_bp.route('/eventos')
def list_events():
    upcoming_events = Event.query.filter(Event.event_date > db.func.now()).order_by(Event.event_date.asc()).all()
    past_events = Event.query.filter(Event.event_date <= db.func.now()).order_by(Event.event_date.desc()).limit(5).all()
    
    return render_template('event/list.html', upcoming_events=upcoming_events, past_events=past_events)


@event_bp.route('/evento/<int:event_id>')
def view_event(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template('event/detail.html', event=event)
