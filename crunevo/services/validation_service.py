from typing import Dict, Any, List, Optional
import re
from datetime import datetime


class ValidationService:
    """Service for validating data across the personal space system."""
    
    # Valid block types
    VALID_BLOCK_TYPES = {
        'nota', 'lista', 'objetivo', 'kanban', 'recordatorio', 
        'frase', 'imagen', 'enlace', 'codigo', 'calendario'
    }
    
    # Valid block statuses
    VALID_BLOCK_STATUSES = {'active', 'archived', 'deleted'}
    
    # Valid template categories
    VALID_TEMPLATE_CATEGORIES = {
        'personal', 'academic', 'work', 'project', 
        'health', 'finance', 'creative', 'other'
    }
    
    @staticmethod
    def validate_block_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate block creation/update data."""
        errors = []
        
        # Validate block type
        block_type = data.get('type')
        if not block_type:
            errors.append('Block type is required')
        elif block_type not in ValidationService.VALID_BLOCK_TYPES:
            errors.append(f'Invalid block type: {block_type}')
        
        # Validate title
        title = data.get('title', '').strip()
        if not title:
            errors.append('Block title is required')
        elif len(title) > 200:
            errors.append('Block title must be 200 characters or less')
        
        # Validate content
        content = data.get('content', '')
        if len(content) > 10000:
            errors.append('Block content must be 10,000 characters or less')
        
        # Validate order_index
        order_index = data.get('order_index')
        if order_index is not None:
            if not isinstance(order_index, int) or order_index < 0:
                errors.append('Order index must be a non-negative integer')
        
        # Validate status
        status = data.get('status')
        if status and status not in ValidationService.VALID_BLOCK_STATUSES:
            errors.append(f'Invalid block status: {status}')
        
        # Validate metadata based on block type
        metadata = data.get('metadata', {})
        if metadata:
            type_errors = ValidationService._validate_block_metadata(block_type, metadata)
            errors.extend(type_errors)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'cleaned_data': {
                'type': block_type,
                'title': title,
                'content': content,
                'metadata': metadata,
                'order_index': order_index,
                'status': status or 'active'
            }
        }
    
    @staticmethod
    def _validate_block_metadata(block_type: str, metadata: Dict[str, Any]) -> List[str]:
        """Validate metadata based on block type."""
        errors = []
        
        if block_type == 'lista':
            tasks = metadata.get('tasks', [])
            if not isinstance(tasks, list):
                errors.append('Lista metadata must contain a tasks array')
            else:
                for i, task in enumerate(tasks):
                    if not isinstance(task, dict):
                        errors.append(f'Task {i} must be an object')
                    elif 'text' not in task:
                        errors.append(f'Task {i} must have a text field')
        
        elif block_type == 'objetivo':
            progress = metadata.get('progress')
            if progress is not None:
                if not isinstance(progress, (int, float)) or progress < 0 or progress > 100:
                    errors.append('Objetivo progress must be between 0 and 100')
            
            status = metadata.get('status')
            if status and status not in ['no_iniciada', 'en_progreso', 'completada', 'pausada']:
                errors.append('Invalid objetivo status')
        
        elif block_type == 'kanban':
            columns = metadata.get('columns', {})
            if not isinstance(columns, dict):
                errors.append('Kanban metadata must contain a columns object')
            else:
                required_columns = ['por_hacer', 'en_progreso', 'hecho']
                for col in required_columns:
                    if col not in columns:
                        errors.append(f'Kanban must have {col} column')
                    elif not isinstance(columns[col], list):
                        errors.append(f'Kanban {col} column must be an array')
        
        elif block_type == 'recordatorio':
            due_date = metadata.get('due_date')
            if due_date:
                try:
                    datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                except ValueError:
                    errors.append('Invalid due_date format')
            
            priority = metadata.get('priority')
            if priority and priority not in ['low', 'medium', 'high', 'urgent']:
                errors.append('Invalid recordatorio priority')
        
        elif block_type == 'enlace':
            url = metadata.get('url')
            if url and not ValidationService._is_valid_url(url):
                errors.append('Invalid URL format')
        
        return errors
    
    @staticmethod
    def validate_template_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate template creation/update data."""
        errors = []
        
        # Validate name
        name = data.get('name', '').strip()
        if not name:
            errors.append('Template name is required')
        elif len(name) > 100:
            errors.append('Template name must be 100 characters or less')
        
        # Validate description
        description = data.get('description', '')
        if len(description) > 500:
            errors.append('Template description must be 500 characters or less')
        
        # Validate category
        category = data.get('category', 'personal')
        if category not in ValidationService.VALID_TEMPLATE_CATEGORIES:
            errors.append(f'Invalid template category: {category}')
        
        # Validate template_data
        template_data = data.get('template_data', {})
        if not isinstance(template_data, dict):
            errors.append('Template data must be an object')
        elif 'blocks' in template_data:
            blocks = template_data['blocks']
            if not isinstance(blocks, list):
                errors.append('Template blocks must be an array')
            else:
                for i, block_data in enumerate(blocks):
                    block_validation = ValidationService.validate_block_data(block_data)
                    if not block_validation['valid']:
                        errors.extend([f'Block {i}: {error}' for error in block_validation['errors']])
        
        # Validate is_public
        is_public = data.get('is_public', False)
        if not isinstance(is_public, bool):
            errors.append('is_public must be a boolean')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'cleaned_data': {
                'name': name,
                'description': description,
                'category': category,
                'template_data': template_data,
                'is_public': is_public
            }
        }
    
    @staticmethod
    def validate_reorder_data(data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate block reorder data."""
        errors = []
        
        if not isinstance(data, list):
            errors.append('Reorder data must be an array')
            return {'valid': False, 'errors': errors}
        
        seen_ids = set()
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                errors.append(f'Item {i} must be an object')
                continue
            
            # Validate id
            block_id = item.get('id')
            if not block_id:
                errors.append(f'Item {i} must have an id')
            elif block_id in seen_ids:
                errors.append(f'Duplicate block id: {block_id}')
            else:
                seen_ids.add(block_id)
            
            # Validate order_index
            order_index = item.get('order_index')
            if order_index is None:
                errors.append(f'Item {i} must have an order_index')
            elif not isinstance(order_index, int) or order_index < 0:
                errors.append(f'Item {i} order_index must be a non-negative integer')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'cleaned_data': data
        }
    
    @staticmethod
    def validate_search_query(query: str) -> Dict[str, Any]:
        """Validate search query."""
        errors = []
        
        if not query or not query.strip():
            errors.append('Search query is required')
        elif len(query) > 100:
            errors.append('Search query must be 100 characters or less')
        
        # Basic sanitization
        cleaned_query = query.strip()
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'cleaned_data': cleaned_query
        }
    
    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """Check if URL is valid."""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'  # domain...
            r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # host...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return bool(url_pattern.match(url))
    
    @staticmethod
    def sanitize_html_content(content: str) -> str:
        """Basic HTML sanitization for content."""
        if not content:
            return ''
        
        # Remove potentially dangerous tags
        dangerous_tags = ['<script', '<iframe', '<object', '<embed', '<form']
        for tag in dangerous_tags:
            content = re.sub(f'{tag}[^>]*>', '', content, flags=re.IGNORECASE)
            content = re.sub(f'</{tag[1:]}>', '', content, flags=re.IGNORECASE)
        
        return content
    
    @staticmethod
    def validate_pagination_params(page: Any, per_page: Any) -> Dict[str, Any]:
        """Validate pagination parameters."""
        errors = []
        
        # Validate page
        try:
            page = int(page) if page is not None else 1
            if page < 1:
                page = 1
        except (ValueError, TypeError):
            page = 1
            errors.append('Invalid page number, using default')
        
        # Validate per_page
        try:
            per_page = int(per_page) if per_page is not None else 20
            if per_page < 1:
                per_page = 20
            elif per_page > 100:
                per_page = 100
                errors.append('per_page limited to 100')
        except (ValueError, TypeError):
            per_page = 20
            errors.append('Invalid per_page, using default')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'cleaned_data': {
                'page': page,
                'per_page': per_page
            }
        }