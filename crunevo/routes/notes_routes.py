import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import cloudinary.uploader
from crunevo.extensions import db
from crunevo.models import Note, Comment
from crunevo.utils.credits import add_credit
from crunevo.utils import unlock_achievement
from crunevo.constants import CreditReasons, AchievementCodes

notes_bp = Blueprint('notes', __name__, url_prefix='/notes')


@notes_bp.route('/')
@login_required
def list_notes():
    notes = Note.query.order_by(Note.created_at.desc()).all()
    return render_template('notes/list.html', notes=notes)


@notes_bp.route('/search')
@login_required
def search_notes():
    q = request.args.get('q', '')
    results = Note.query.filter(
        (Note.title.ilike(f'%{q}%')) | (Note.tags.ilike(f'%{q}%'))
    ).all()
    return jsonify([
        {'id': n.id, 'title': n.title, 'description': n.description}
        for n in results
    ])


@notes_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_note():
    if request.method == 'POST':
        f = request.files['file']
        cloud_url = current_app.config.get('CLOUDINARY_URL')
        if cloud_url:
            result = cloudinary.uploader.upload(f)
            filepath = result['secure_url']
        else:
            filename = secure_filename(f.filename)
            upload_folder = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            filepath = os.path.join(upload_folder, filename)
            f.save(filepath)
        note = Note(title=request.form['title'],
                    description=request.form['description'],
                    filename=filepath,
                    tags=request.form.get('tags'),
                    category=request.form.get('category'),
                    author=current_user)
        db.session.add(note)
        current_user.points += 10
        db.session.commit()
        add_credit(current_user, 5, CreditReasons.APUNTE_SUBIDO, related_id=note.id)
        unlock_achievement(current_user, AchievementCodes.PRIMER_APUNTE)
        flash('Apunte subido correctamente')
        return redirect(url_for('notes.list_notes'))
    return render_template('notes/upload.html')


@notes_bp.route('/<int:note_id>')
@login_required
def detail(note_id):
    note = Note.query.get_or_404(note_id)
    note.views += 1
    db.session.commit()
    return render_template('notes/detalle.html', note=note)


@notes_bp.route('/<int:note_id>/comment', methods=['POST'])
@login_required
def add_comment(note_id):
    note = Note.query.get_or_404(note_id)
    body = request.form['body']
    comment = Comment(body=body, author=current_user, note=note)
    db.session.add(comment)
    db.session.commit()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'body': comment.body,
            'author': comment.author.username,
            'timestamp': comment.timestamp.strftime('%Y-%m-%d %H:%M')
        })
    return redirect(url_for('notes.detail', note_id=note_id))

