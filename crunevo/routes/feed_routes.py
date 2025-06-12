import os
import cloudinary.uploader
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from datetime import datetime
from crunevo.extensions import db
from crunevo.models import Note, Post, FeedItem

feed_bp = Blueprint('feed', __name__)


@feed_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        content = request.form['content']
        image = request.files.get('image')
        image_url = None
        if image and image.filename:
            cloud_url = current_app.config.get('CLOUDINARY_URL')
            if cloud_url:
                result = cloudinary.uploader.upload(image)
                image_url = result['secure_url']
            else:
                filename = secure_filename(image.filename)
                upload_folder = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                image.save(filepath)
                image_url = filepath
        post = Post(content=content, image_url=image_url, author=current_user)
        db.session.add(post)
        db.session.commit()
        from crunevo.utils import create_feed_item_for_all
        create_feed_item_for_all('post', post.id)
        flash('Publicación creada')
        return redirect(url_for('feed.index'))
    return render_template('feed/index.html')


@feed_bp.route('/trending')
@login_required
def trending():
    posts = Post.query.order_by(Post.created_at.desc()).limit(10).all()
    today = datetime.utcnow().date()
    return render_template('feed/feed.html', posts=posts, trending=True, today=today)


@feed_bp.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    question = request.json.get('question')
    # placeholder for future AI integration
    return jsonify({'answer': f'Respuesta a "{question}"'})


@feed_bp.route('/api/analizar', methods=['POST'])
@login_required
def api_analizar():
    text = request.json.get('text')
    return jsonify({'analysis': f'Analisis simple de {len(text)} caracteres'})


@feed_bp.route('/api/feed')
@login_required
def api_feed():
    page = int(request.args.get('page', 1))
    q = (FeedItem.query
         .filter_by(owner_id=current_user.id)
         .order_by(FeedItem.score.desc(), FeedItem.created_at.desc())
         .paginate(page=page, per_page=10, error_out=False))
    return jsonify([fi.to_dict() for fi in q.items])
