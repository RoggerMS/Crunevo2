from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, date
import re
import json
from flask import current_app
import logging


class ValidationError(Exception):
    """Custom validation error with detailed information."""
    
    def __init__(self, message: str, field: str = None, code: str = None):
        self.message = message
        self.field = field
        self.code = code
        super().__init__(message)


class ValidationService:
    """Comprehensive validation service for personal space data."""
    
    # Common validation patterns
    PATTERNS = {
        'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
        'uuid': re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'),
        'color_hex': re.compile(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'),
        'slug': re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$'),
        'safe_html': re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL)
    }
    
    # Allowed HTML tags for content
    ALLOWED_HTML_TAGS = {
        'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'h1', 'h2', 'h3', 
        'h4', 'h5', 'h6', 'blockquote', 'code', 'pre', 'a', 'img'
    }
    
    # Block type specific configurations
    BLOCK_VALIDATIONS = {
        'tarea': {
            'title': {'required': True, 'max_length': 255, 'min_length': 1},
            'content': {'max_length': 5000},
            'priority': {'choices': ['low', 'medium', 'high', 'urgent']},
            'status': {'choices': ['pending', 'in_progress', 'completed', 'cancelled']},
            'due_date': {'type': 'datetime'},
            'estimated_duration': {'type': 'integer', 'min': 1, 'max': 1440}  # minutes
        },
        'objetivo': {
            'title': {'required': True, 'max_length': 255, 'min_length': 1},
            'content': {'max_length': 10000},
            'progress': {'type': 'integer', 'min': 0, 'max': 100},
            'status': {'choices': ['no_iniciada', 'en_progreso', 'cumplida', 'pausada']},
            'target_date': {'type': 'date'},
            'difficulty': {'choices': ['easy', 'medium', 'hard', 'expert']}
        },
        'nota': {
            'title': {'required': True, 'max_length': 255, 'min_length': 1},
            'content': {'max_length': 50000},
            'category': {'max_length': 100},
            'tags': {'type': 'list', 'max_items': 10}
        },
        'lista': {
            'title': {'required': True, 'max_length': 255, 'min_length': 1},
            'content': {'max_length': 10000},
            'tasks': {'type': 'list', 'max_items': 100},
            'list_type': {'choices': ['checklist', 'numbered', 'bulleted']}
        },
        'kanban': {
            'title': {'required': True, 'max_length': 255, 'min_length': 1},
            'content': {'max_length': 20000},
            'columns': {'type': 'dict', 'required': True},
            'max_cards_per_column': {'type': 'integer', 'min': 1, 'max': 50}
        },
        'recordatorio': {
            'title': {'required': True, 'max_length': 255, 'min_length': 1},
            'content': {'max_length': 2000},
            'due_date': {'type': 'datetime', 'required': True},
            'priority': {'choices': ['low', 'medium', 'high', 'urgent']},
            'repeat_type': {'choices': ['none', 'daily', 'weekly', 'monthly', 'yearly']}
        }
    }
    
    @classmethod
    def validate_block_data(cls, block_data: Dict[str, Any], block_type: str = None) -> Dict[str, Any]:
        """Validate complete block data with comprehensive checks."""
        errors = []
        warnings = []
        cleaned_data = {}
        
        try:
            # Determine block type
            if not block_type:
                block_type = block_data.get('type')
            
            if not block_type or block_type not in cls.BLOCK_VALIDATIONS:
                errors.append({
                    'field': 'type',
                    'message': f'Invalid or missing block type: {block_type}',
                    'code': 'INVALID_TYPE'
                })
                return cls._format_validation_result(False, errors, warnings, {})
            
            cleaned_data['type'] = block_type
            validation_config = cls.BLOCK_VALIDATIONS[block_type]
            
            # Validate each field
            for field_name, field_config in validation_config.items():
                field_value = block_data.get(field_name)
                
                try:
                    validated_value, field_errors, field_warnings = cls._validate_field(
                        field_name, field_value, field_config
                    )
                    
                    if field_errors:
                        errors.extend(field_errors)
                    else:
                        cleaned_data[field_name] = validated_value
                    
                    if field_warnings:
                        warnings.extend(field_warnings)
                        
                except Exception as e:
                    errors.append({
                        'field': field_name,
                        'message': f'Validation error: {str(e)}',
                        'code': 'VALIDATION_ERROR'
                    })
            
            # Cross-field validation
            cross_validation_errors = cls._cross_validate_fields(cleaned_data, block_type)
            errors.extend(cross_validation_errors)
            
            # Security validation
            security_errors = cls._validate_security(cleaned_data)
            errors.extend(security_errors)
            
            return cls._format_validation_result(
                len(errors) == 0, errors, warnings, cleaned_data
            )
            
        except Exception as e:
            logging.error(f"Unexpected error in block validation: {str(e)}")
            errors.append({
                'field': 'general',
                'message': 'An unexpected validation error occurred',
                'code': 'UNEXPECTED_ERROR'
            })
            return cls._format_validation_result(False, errors, warnings, {})
    
    @classmethod
    def _validate_field(cls, field_name: str, field_value: Any, 
                       field_config: Dict[str, Any]) -> Tuple[Any, List[Dict], List[Dict]]:
        """Validate a single field with its configuration."""
        errors = []
        warnings = []
        
        # Handle required fields
        if field_config.get('required', False) and (field_value is None or field_value == ''):
            errors.append({
                'field': field_name,
                'message': f'{field_name} is required',
                'code': 'REQUIRED_FIELD'
            })
            return None, errors, warnings
        
        # Skip validation if field is None and not required
        if field_value is None:
            return None, errors, warnings
        
        # Type validation
        field_type = field_config.get('type', 'string')
        validated_value, type_errors = cls._validate_type(field_name, field_value, field_type)
        
        if type_errors:
            errors.extend(type_errors)
            return None, errors, warnings
        
        # Length validation for strings
        if isinstance(validated_value, str):
            length_errors, length_warnings = cls._validate_string_length(
                field_name, validated_value, field_config
            )
            errors.extend(length_errors)
            warnings.extend(length_warnings)
        
        # Choice validation
        if 'choices' in field_config:
            if validated_value not in field_config['choices']:
                errors.append({
                    'field': field_name,
                    'message': f'{field_name} must be one of: {", ".join(field_config["choices"])}',
                    'code': 'INVALID_CHOICE'
                })
        
        # Range validation for numbers
        if isinstance(validated_value, (int, float)):
            range_errors = cls._validate_number_range(field_name, validated_value, field_config)
            errors.extend(range_errors)
        
        # List validation
        if field_type == 'list' and isinstance(validated_value, list):
            list_errors, list_warnings = cls._validate_list(
                field_name, validated_value, field_config
            )
            errors.extend(list_errors)
            warnings.extend(list_warnings)
        
        return validated_value, errors, warnings
    
    @classmethod
    def _validate_type(cls, field_name: str, field_value: Any, expected_type: str) -> Tuple[Any, List[Dict]]:
        """Validate and convert field type."""
        errors = []
        
        try:
            if expected_type == 'string':
                return str(field_value), errors
            
            elif expected_type == 'integer':
                if isinstance(field_value, int):
                    return field_value, errors
                elif isinstance(field_value, str) and field_value.isdigit():
                    return int(field_value), errors
                else:
                    errors.append({
                        'field': field_name,
                        'message': f'{field_name} must be an integer',
                        'code': 'INVALID_INTEGER'
                    })
            
            elif expected_type == 'float':
                return float(field_value), errors
            
            elif expected_type == 'boolean':
                if isinstance(field_value, bool):
                    return field_value, errors
                elif isinstance(field_value, str):
                    return field_value.lower() in ('true', '1', 'yes', 'on'), errors
                else:
                    return bool(field_value), errors
            
            elif expected_type == 'list':
                if isinstance(field_value, list):
                    return field_value, errors
                elif isinstance(field_value, str):
                    try:
                        return json.loads(field_value), errors
                    except json.JSONDecodeError:
                        errors.append({
                            'field': field_name,
                            'message': f'{field_name} must be a valid list',
                            'code': 'INVALID_LIST'
                        })
            
            elif expected_type == 'dict':
                if isinstance(field_value, dict):
                    return field_value, errors
                elif isinstance(field_value, str):
                    try:
                        return json.loads(field_value), errors
                    except json.JSONDecodeError:
                        errors.append({
                            'field': field_name,
                            'message': f'{field_name} must be a valid object',
                            'code': 'INVALID_OBJECT'
                        })
            
            elif expected_type == 'datetime':
                if isinstance(field_value, datetime):
                    return field_value, errors
                elif isinstance(field_value, str):
                    try:
                        return datetime.fromisoformat(field_value.replace('Z', '+00:00')), errors
                    except ValueError:
                        errors.append({
                            'field': field_name,
                            'message': f'{field_name} must be a valid datetime',
                            'code': 'INVALID_DATETIME'
                        })
            
            elif expected_type == 'date':
                if isinstance(field_value, date):
                    return field_value, errors
                elif isinstance(field_value, str):
                    try:
                        return datetime.fromisoformat(field_value).date(), errors
                    except ValueError:
                        errors.append({
                            'field': field_name,
                            'message': f'{field_name} must be a valid date',
                            'code': 'INVALID_DATE'
                        })
            
            return field_value, errors
            
        except Exception as e:
            errors.append({
                'field': field_name,
                'message': f'Type conversion error: {str(e)}',
                'code': 'TYPE_CONVERSION_ERROR'
            })
            return None, errors
    
    @classmethod
    def _validate_string_length(cls, field_name: str, field_value: str, 
                               field_config: Dict[str, Any]) -> Tuple[List[Dict], List[Dict]]:
        """Validate string length constraints."""
        errors = []
        warnings = []
        
        length = len(field_value)
        
        if 'min_length' in field_config and length < field_config['min_length']:
            errors.append({
                'field': field_name,
                'message': f'{field_name} must be at least {field_config["min_length"]} characters',
                'code': 'MIN_LENGTH'
            })
        
        if 'max_length' in field_config and length > field_config['max_length']:
            errors.append({
                'field': field_name,
                'message': f'{field_name} cannot exceed {field_config["max_length"]} characters',
                'code': 'MAX_LENGTH'
            })
        
        # Warning for very long content
        if length > field_config.get('max_length', 1000) * 0.8:
            warnings.append({
                'field': field_name,
                'message': f'{field_name} is approaching the maximum length limit',
                'code': 'LENGTH_WARNING'
            })
        
        return errors, warnings
    
    @classmethod
    def _validate_number_range(cls, field_name: str, field_value: Union[int, float], 
                              field_config: Dict[str, Any]) -> List[Dict]:
        """Validate number range constraints."""
        errors = []
        
        if 'min' in field_config and field_value < field_config['min']:
            errors.append({
                'field': field_name,
                'message': f'{field_name} must be at least {field_config["min"]}',
                'code': 'MIN_VALUE'
            })
        
        if 'max' in field_config and field_value > field_config['max']:
            errors.append({
                'field': field_name,
                'message': f'{field_name} cannot exceed {field_config["max"]}',
                'code': 'MAX_VALUE'
            })
        
        return errors
    
    @classmethod
    def _validate_list(cls, field_name: str, field_value: List[Any], 
                      field_config: Dict[str, Any]) -> Tuple[List[Dict], List[Dict]]:
        """Validate list constraints."""
        errors = []
        warnings = []
        
        if 'max_items' in field_config and len(field_value) > field_config['max_items']:
            errors.append({
                'field': field_name,
                'message': f'{field_name} cannot have more than {field_config["max_items"]} items',
                'code': 'MAX_ITEMS'
            })
        
        if 'min_items' in field_config and len(field_value) < field_config['min_items']:
            errors.append({
                'field': field_name,
                'message': f'{field_name} must have at least {field_config["min_items"]} items',
                'code': 'MIN_ITEMS'
            })
        
        return errors, warnings
    
    @classmethod
    def _cross_validate_fields(cls, cleaned_data: Dict[str, Any], block_type: str) -> List[Dict]:
        """Perform cross-field validation."""
        errors = []
        
        # Date consistency validation
        if 'due_date' in cleaned_data and 'target_date' in cleaned_data:
            if cleaned_data['due_date'] and cleaned_data['target_date']:
                if cleaned_data['due_date'].date() > cleaned_data['target_date']:
                    errors.append({
                        'field': 'due_date',
                        'message': 'Due date cannot be after target date',
                        'code': 'DATE_INCONSISTENCY'
                    })
        
        # Progress and status consistency
        if block_type == 'objetivo':
            progress = cleaned_data.get('progress', 0)
            status = cleaned_data.get('status')
            
            if progress == 100 and status != 'cumplida':
                errors.append({
                    'field': 'status',
                    'message': 'Status should be "cumplida" when progress is 100%',
                    'code': 'PROGRESS_STATUS_MISMATCH'
                })
            elif progress == 0 and status == 'cumplida':
                errors.append({
                    'field': 'progress',
                    'message': 'Progress should be greater than 0% when status is "cumplida"',
                    'code': 'PROGRESS_STATUS_MISMATCH'
                })
        
        # Kanban columns validation
        if block_type == 'kanban' and 'columns' in cleaned_data:
            columns = cleaned_data['columns']
            if not isinstance(columns, dict) or len(columns) < 2:
                errors.append({
                    'field': 'columns',
                    'message': 'Kanban board must have at least 2 columns',
                    'code': 'INSUFFICIENT_COLUMNS'
                })
        
        return errors
    
    @classmethod
    def _validate_security(cls, cleaned_data: Dict[str, Any]) -> List[Dict]:
        """Validate security constraints."""
        errors = []
        
        # Check for potentially dangerous content
        for field_name, field_value in cleaned_data.items():
            if isinstance(field_value, str):
                # Check for script tags
                if cls.PATTERNS['safe_html'].search(field_value):
                    errors.append({
                        'field': field_name,
                        'message': f'{field_name} contains potentially unsafe content',
                        'code': 'UNSAFE_CONTENT'
                    })
                
                # Check for very long strings that might cause DoS
                if len(field_value) > 100000:  # 100KB limit
                    errors.append({
                        'field': field_name,
                        'message': f'{field_name} is too large',
                        'code': 'CONTENT_TOO_LARGE'
                    })
        
        return errors
    
    @classmethod
    def _format_validation_result(cls, is_valid: bool, errors: List[Dict], 
                                 warnings: List[Dict], cleaned_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format the validation result consistently."""
        return {
            'valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'cleaned_data': cleaned_data,
            'error_count': len(errors),
            'warning_count': len(warnings)
        }
    
    @classmethod
    def validate_user_input(cls, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate general user input with sanitization."""
        errors = []
        cleaned_data = {}
        
        for field_name, field_value in input_data.items():
            if isinstance(field_value, str):
                # Basic sanitization
                cleaned_value = field_value.strip()
                
                # Remove null bytes
                cleaned_value = cleaned_value.replace('\x00', '')
                
                # Limit length
                if len(cleaned_value) > 10000:
                    errors.append({
                        'field': field_name,
                        'message': f'{field_name} is too long',
                        'code': 'INPUT_TOO_LONG'
                    })
                    continue
                
                cleaned_data[field_name] = cleaned_value
            else:
                cleaned_data[field_name] = field_value
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'cleaned_data': cleaned_data
        }
    
    @classmethod
    def validate_api_request(cls, request_data: Dict[str, Any], 
                           required_fields: List[str] = None) -> Dict[str, Any]:
        """Validate API request data."""
        errors = []
        
        # Check required fields
        if required_fields:
            for field in required_fields:
                if field not in request_data or request_data[field] is None:
                    errors.append({
                        'field': field,
                        'message': f'{field} is required',
                        'code': 'REQUIRED_FIELD'
                    })
        
        # Validate request size
        try:
            request_size = len(json.dumps(request_data))
            if request_size > 1024 * 1024:  # 1MB limit
                errors.append({
                    'field': 'request',
                    'message': 'Request payload is too large',
                    'code': 'PAYLOAD_TOO_LARGE'
                })
        except Exception:
            errors.append({
                'field': 'request',
                'message': 'Invalid request format',
                'code': 'INVALID_FORMAT'
            })
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }