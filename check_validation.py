#!/usr/bin/env python3
import sys
sys.path.append('C:\\Users\\bestr\\OneDrive\\Desktop\\git\\Crunevo2')

from crunevo.services.validation_service import ValidationService

print('Campos requeridos por tipo de bloque:')
print('=' * 50)

for block_type, validations in ValidationService.BLOCK_VALIDATIONS.items():
    required_fields = [field for field, config in validations.items() if config.get('required', False)]
    print(f'{block_type}: {required_fields}')

print('\nEjemplo de datos que envía el frontend:')
print('=' * 50)
frontend_data = {
    'type': 'tarea',
    'title': 'Nueva tarea',
    'description': 'Descripción de la tarea',  # Frontend envía 'description'
    'category': 'personal',
    'priority': 'medium',
    'size': 'medium',
    'position_x': 0,
    'position_y': 0,
    'theme_color': 'blue',
    'header_style': 'default',
    'show_border': False,
    'show_shadow': False,
    'auto_save': False,
    'notifications': False,
    'collaborative': False,
    'public_view': False,
    'type_specific_config': {}
}

print('Datos del frontend:')
for key, value in frontend_data.items():
    print(f'  {key}: {value}')

print('\nValidación esperada para "tarea":')
for field, config in ValidationService.BLOCK_VALIDATIONS['tarea'].items():
    print(f'  {field}: {config}')