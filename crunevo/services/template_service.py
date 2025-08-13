from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy import and_, or_
from crunevo.extensions import db
from crunevo.models import PersonalSpaceTemplate, PersonalSpaceBlock
from crunevo.services.block_service import BlockService
from crunevo.services.validation_service import ValidationService
from crunevo.services.cache_service import CacheInvalidator


class TemplateService:
    """Service for managing personal space templates."""

    @staticmethod
    def create_template(user_id: int, template_data: Dict[str, Any]) -> PersonalSpaceTemplate:
        """Create a new template from user data."""
        # Validate template data
        validation_result = ValidationService.validate_template_data(template_data)
        if not validation_result['valid']:
            raise ValueError(f"Validation errors: {', '.join(validation_result['errors'])}")
        
        cleaned_data = validation_result['cleaned_data']
        
        template = PersonalSpaceTemplate(
            user_id=user_id,
            name=cleaned_data['name'],
            description=cleaned_data['description'],
            template_data=cleaned_data['template_data'],
            category=cleaned_data['category'],
            is_public=cleaned_data['is_public']
        )
        
        db.session.add(template)
        db.session.commit()
        
        # Invalidate cache
        CacheInvalidator.on_template_change(user_id)
        
        return template
    
    @staticmethod
    def create_template_from_workspace(user_id: int, name: str, description: str = '', 
                                     category: str = 'personal', is_public: bool = False) -> PersonalSpaceTemplate:
        """Create a template from user's current workspace."""
        # Get user's active blocks
        blocks = PersonalSpaceBlock.query.filter_by(
            user_id=user_id, status='active'
        ).order_by(PersonalSpaceBlock.order_index.asc()).all()
        
        if not blocks:
            raise ValueError("No blocks found to create template")
        
        # Convert blocks to template data
        template_blocks = []
        for block in blocks:
            template_blocks.append({
                'type': block.type,
                'title': block.title,
                'content': block.content,
                'metadata': block.metadata_json or {},
                'order_index': block.order_index
            })
        
        template_data = {
            'blocks': template_blocks,
            'layout': 'grid',  # Default layout
            'created_from_workspace': True,
            'original_block_count': len(blocks)
        }
        
        template = PersonalSpaceTemplate(
            user_id=user_id,
            name=name,
            description=description,
            template_data=template_data,
            category=category,
            is_public=is_public
        )
        
        db.session.add(template)
        db.session.commit()
        return template
    
    @staticmethod
    def apply_template(template_id: str, user_id: int, replace_existing: bool = False) -> List[PersonalSpaceBlock]:
        """Apply a template to user's workspace."""
        template = PersonalSpaceTemplate.query.filter(
            and_(
                PersonalSpaceTemplate.id == template_id,
                or_(
                    PersonalSpaceTemplate.is_public.is_(True),
                    PersonalSpaceTemplate.user_id == user_id
                )
            )
        ).first()
        
        if not template:
            raise ValueError("Template not found or not accessible")
        
        # If replace_existing, delete current blocks
        if replace_existing:
            existing_blocks = PersonalSpaceBlock.query.filter_by(
                user_id=user_id, status='active'
            ).all()
            for block in existing_blocks:
                block.status = 'deleted'
        
        # Create blocks from template
        created_blocks = []
        template_blocks = template.template_data.get('blocks', [])
        
        for block_data in template_blocks:
            try:
                block = BlockService.create_block(user_id, block_data)
                created_blocks.append(block)
            except Exception as e:
                # Log error but continue with other blocks
                print(f"Error creating block from template: {e}")
                continue
        
        db.session.commit()
        return created_blocks
    
    @staticmethod
    def get_templates(user_id: int, category: Optional[str] = None, 
                     include_public: bool = True) -> List[PersonalSpaceTemplate]:
        """Get templates available to user."""
        query = PersonalSpaceTemplate.query
        
        if include_public:
            query = query.filter(
                or_(
                    PersonalSpaceTemplate.user_id == user_id,
                      PersonalSpaceTemplate.is_public.is_(True)
                )
            )
        else:
            query = query.filter_by(user_id=user_id)
        
        if category:
            query = query.filter_by(category=category)
        
        return query.order_by(PersonalSpaceTemplate.created_at.desc()).all()
    
    @staticmethod
    def get_template_categories() -> List[Dict[str, Any]]:
        """Get available template categories with counts."""
        categories = db.session.query(
            PersonalSpaceTemplate.category,
            db.func.count(PersonalSpaceTemplate.id).label('count')
        ).filter(
            PersonalSpaceTemplate.is_public.is_(True)
        ).group_by(PersonalSpaceTemplate.category).all()
        
        return [
            {
                'name': category,
                'count': count,
                'display_name': TemplateService._get_category_display_name(category)
            }
            for category, count in categories
        ]
    
    @staticmethod
    def _get_category_display_name(category: str) -> str:
        """Get display name for category."""
        category_names = {
            'personal': 'Personal',
            'academic': 'Académico',
            'work': 'Trabajo',
            'project': 'Proyectos',
            'health': 'Salud',
            'finance': 'Finanzas',
            'creative': 'Creativo',
            'other': 'Otros'
        }
        return category_names.get(category, category.title())
    
    @staticmethod
    def update_template(template_id: str, user_id: int, update_data: Dict[str, Any]) -> PersonalSpaceTemplate:
        """Update a template (only owner can update)."""
        template = PersonalSpaceTemplate.query.filter_by(
            id=template_id, user_id=user_id
        ).first()
        
        if not template:
            raise ValueError("Template not found or not owned by user")
        
        # Prepare current data for validation
        current_data = {
            'name': update_data.get('name', template.name),
            'description': update_data.get('description', template.description),
            'category': update_data.get('category', template.category),
            'template_data': update_data.get('template_data', template.template_data),
            'is_public': update_data.get('is_public', template.is_public)
        }
        
        # Validate update data
        validation_result = ValidationService.validate_template_data(current_data)
        if not validation_result['valid']:
            raise ValueError(f"Validation errors: {', '.join(validation_result['errors'])}")
        
        cleaned_data = validation_result['cleaned_data']
        
        # Update fields
        for field in ['name', 'description', 'category', 'is_public']:
            if field in update_data:
                setattr(template, field, cleaned_data[field])
        
        if 'template_data' in update_data:
            template.template_data = cleaned_data['template_data']
        
        template.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Invalidate cache
        CacheInvalidator.on_template_change(user_id)
        
        return template
    
    @staticmethod
    def delete_template(template_id: str, user_id: int) -> bool:
        """Delete a template (only owner can delete)."""
        template = PersonalSpaceTemplate.query.filter_by(
            id=template_id, user_id=user_id
        ).first()
        
        if not template:
            return False
        
        db.session.delete(template)
        db.session.commit()
        
        # Invalidate cache
        CacheInvalidator.on_template_change(user_id)
        
        return True
    
    @staticmethod
    def get_popular_templates(limit: int = 10) -> List[PersonalSpaceTemplate]:
        """Get most popular public templates."""
        # For now, just return recent public templates
        # In a real app, you'd track usage/downloads
        return PersonalSpaceTemplate.query.filter_by(
            is_public=True
        ).order_by(
            PersonalSpaceTemplate.created_at.desc()
        ).limit(limit).all()
    
    @staticmethod
    def search_templates(query: str, user_id: int) -> List[PersonalSpaceTemplate]:
        """Search templates by name and description."""
        # Validate search query
        validation_result = ValidationService.validate_search_query(query)
        if not validation_result['valid']:
            raise ValueError(f"Validation errors: {', '.join(validation_result['errors'])}")
        
        cleaned_query = validation_result['cleaned_data']
        search_pattern = f"%{cleaned_query}%"
        
        return PersonalSpaceTemplate.query.filter(
            and_(
                or_(
                    PersonalSpaceTemplate.user_id == user_id,
                    PersonalSpaceTemplate.is_public.is_(True)
                ),
                or_(
                    PersonalSpaceTemplate.name.ilike(search_pattern),
                    PersonalSpaceTemplate.description.ilike(search_pattern)
                )
            )
        ).order_by(PersonalSpaceTemplate.updated_at.desc()).all()
    
    @staticmethod
    def get_default_templates() -> List[Dict[str, Any]]:
        """Get default system templates."""
        return [
            {
                'id': 'default_student',
                'name': 'Estudiante',
                'description': 'Template básico para estudiantes con tareas, objetivos y notas',
                'category': 'academic',
                'template_data': {
                    'blocks': [
                        {
                            'type': 'objetivo',
                            'title': 'Objetivos del semestre',
                            'content': 'Define tus metas académicas',
                            'metadata': {'progress': 0, 'status': 'no_iniciada'},
                            'order_index': 1
                        },
                        {
                            'type': 'lista',
                            'title': 'Tareas pendientes',
                            'content': 'Lista de tareas por hacer',
                            'metadata': {'tasks': []},
                            'order_index': 2
                        },
                        {
                            'type': 'nota',
                            'title': 'Notas importantes',
                            'content': 'Apuntes y recordatorios',
                            'metadata': {},
                            'order_index': 3
                        }
                    ]
                }
            },
            {
                'id': 'default_work',
                'name': 'Profesional',
                'description': 'Template para profesionales con proyectos y seguimiento',
                'category': 'work',
                'template_data': {
                    'blocks': [
                        {
                            'type': 'kanban',
                            'title': 'Proyectos en curso',
                            'content': 'Gestión de proyectos',
                            'metadata': {
                                'columns': {
                                    'por_hacer': [],
                                    'en_progreso': [],
                                    'hecho': []
                                }
                            },
                            'order_index': 1
                        },
                        {
                            'type': 'objetivo',
                            'title': 'Objetivos trimestrales',
                            'content': 'Metas profesionales',
                            'metadata': {'progress': 0, 'status': 'no_iniciada'},
                            'order_index': 2
                        }
                    ]
                }
            },
            {
                'id': 'default_personal',
                'name': 'Personal',
                'description': 'Template para organización personal y hábitos',
                'category': 'personal',
                'template_data': {
                    'blocks': [
                        {
                            'type': 'lista',
                            'title': 'Hábitos diarios',
                            'content': 'Seguimiento de hábitos',
                            'metadata': {'tasks': []},
                            'order_index': 1
                        },
                        {
                            'type': 'recordatorio',
                            'title': 'Recordatorios importantes',
                            'content': 'No olvides...',
                            'metadata': {'priority': 'medium'},
                            'order_index': 2
                        },
                        {
                            'type': 'frase',
                            'title': 'Motivación diaria',
                            'content': 'Tu frase inspiradora del día',
                            'metadata': {},
                            'order_index': 3
                        }
                    ]
                }
            }
        ]