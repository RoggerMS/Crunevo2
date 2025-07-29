import re
import hashlib
import time
from typing import Dict, List, Optional
from flask import request, current_app
from flask_login import current_user
from crunevo.extensions import db, limiter

# Rate limiting configurations
RATE_LIMITS = {
    'upload_file': '10/minute',
    'create_post': '20/minute',
    'comment': '30/minute',
    'like': '50/minute',
    'search': '60/minute',
    'api_calls': '100/minute'
}

# Content filtering patterns
INAPPROPRIATE_PATTERNS = [
    r'\b(spam|scam|fake)\b',
    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
    r'\b(adult|porn|xxx)\b',
    r'\b(drugs|illegal)\b'
]

def validate_file_upload(file, max_size_mb: int = 10) -> Dict[str, any]:
    """Validate file upload with security checks."""
    if not file:
        return {'valid': False, 'error': 'No file provided'}
    
    # Check file size
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset to beginning
    
    max_size = max_size_mb * 1024 * 1024
    if size > max_size:
        return {'valid': False, 'error': f'File too large. Max size: {max_size_mb}MB'}
    
    # Check file extension
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx'}
    filename = file.filename.lower()
    if not any(filename.endswith(ext) for ext in allowed_extensions):
        return {'valid': False, 'error': 'File type not allowed'}
    
    # Check for malicious content in filename
    if re.search(r'[<>:"/\\|?*]', filename):
        return {'valid': False, 'error': 'Invalid filename'}
    
    return {'valid': True, 'filename': filename, 'size': size}

def sanitize_content(content: str, max_length: int = 5000) -> Dict[str, any]:
    """Sanitize user content with security checks."""
    if not content:
        return {'valid': False, 'error': 'Content is required'}
    
    # Check length
    if len(content) > max_length:
        return {'valid': False, 'error': f'Content too long. Max: {max_length} characters'}
    
    # Check for inappropriate content
    content_lower = content.lower()
    for pattern in INAPPROPRIATE_PATTERNS:
        if re.search(pattern, content_lower):
            return {'valid': False, 'error': 'Content contains inappropriate material'}
    
    # Basic HTML sanitization (if needed)
    # Remove potentially dangerous HTML tags
    dangerous_tags = ['script', 'iframe', 'object', 'embed']
    for tag in dangerous_tags:
        content = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', content, flags=re.IGNORECASE)
        content = re.sub(f'<{tag}[^>]*/?>', '', content, flags=re.IGNORECASE)
    
    return {'valid': True, 'content': content.strip()}

def check_user_permissions(user, action: str) -> bool:
    """Check if user has permission for specific action."""
    if not user or not user.is_authenticated:
        return False
    
    # Admin can do everything
    if user.role == 'admin':
        return True
    
    # Moderator permissions
    if user.role == 'moderator':
        moderator_actions = ['moderate_content', 'view_reports', 'edit_posts']
        if action in moderator_actions:
            return True
    
    # Student permissions
    student_actions = ['create_post', 'upload_file', 'comment', 'like']
    if action in student_actions:
        return user.activated
    
    return False

def log_security_event(event_type: str, user_id: Optional[int] = None, details: Dict = None):
    """Log security events for monitoring."""
    try:
        from crunevo.models import SecurityLog
        
        log_entry = SecurityLog(
            event_type=event_type,
            user_id=user_id or (current_user.id if current_user.is_authenticated else None),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            details=details or {}
        )
        db.session.add(log_entry)
        db.session.commit()
        
        current_app.logger.info(f"Security event: {event_type} by user {user_id}")
    except Exception as e:
        current_app.logger.error(f"Failed to log security event: {e}")

def get_user_activity_score(user_id: int) -> float:
    """Calculate user activity score for rate limiting."""
    try:
        from crunevo.models import Post, Note, Comment
        
        # Count recent activities
        recent_posts = Post.query.filter_by(author_id=user_id).count()
        recent_notes = Note.query.filter_by(user_id=user_id).count()
        recent_comments = Comment.query.filter_by(author_id=user_id).count()
        
        # Calculate score (higher score = more restrictions)
        score = (recent_posts * 0.3) + (recent_notes * 0.5) + (recent_comments * 0.1)
        return min(score, 10.0)  # Cap at 10
    except Exception:
        return 1.0

def apply_dynamic_rate_limit(user_id: int, action: str) -> str:
    """Apply dynamic rate limiting based on user activity."""
    base_limit = RATE_LIMITS.get(action, '30/minute')
    
    # Get user activity score
    activity_score = get_user_activity_score(user_id)
    
    # Adjust rate limit based on activity
    if activity_score > 5:
        # Reduce limit for very active users
        return base_limit.replace('minute', '2minutes')
    elif activity_score < 2:
        # Increase limit for inactive users
        return base_limit.replace('minute', '30seconds')
    
    return base_limit

def validate_csrf_token() -> bool:
    """Validate CSRF token with additional security checks."""
    try:
        from flask_wtf.csrf import validate_csrf
        validate_csrf(request.form.get('csrf_token'))
        return True
    except Exception:
        return False

def check_content_duplication(content: str, user_id: int, content_type: str = 'post') -> bool:
    """Check for duplicate content to prevent spam."""
    try:
        from crunevo.models import Post, Note
        
        # Create content hash
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        # Check recent content by same user
        if content_type == 'post':
            recent_posts = Post.query.filter_by(
                author_id=user_id
            ).order_by(Post.created_at.desc()).limit(5).all()
            
            for post in recent_posts:
                post_hash = hashlib.md5(post.content.encode()).hexdigest()
                if post_hash == content_hash:
                    return True
        elif content_type == 'note':
            recent_notes = Note.query.filter_by(
                user_id=user_id
            ).order_by(Note.created_at.desc()).limit(5).all()
            
            for note in recent_notes:
                note_hash = hashlib.md5(note.description.encode()).hexdigest()
                if note_hash == content_hash:
                    return True
        
        return False
    except Exception:
        return False 