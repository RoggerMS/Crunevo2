from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, URL, Length


class ClubForm(FlaskForm):
    name = StringField("Nombre del Club", validators=[DataRequired(), Length(min=3, max=100)])
    career = StringField("Carrera", validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField("Descripción", validators=[Optional(), Length(max=1000)])
    
    # File upload fields
    avatar = FileField(
        "Avatar del Club", 
        validators=[
            Optional(),
            FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Solo se permiten archivos de imagen (JPG, PNG, GIF)')
        ]
    )
    banner = FileField(
        "Banner del Club", 
        validators=[
            Optional(),
            FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Solo se permiten archivos de imagen (JPG, PNG, GIF)')
        ]
    )
    
    # Social media links
    facebook_url = StringField(
        "Enlace de Facebook", 
        validators=[
            Optional(), 
            URL(message="Debe ser una URL válida"),
            Length(max=255)
        ]
    )
    whatsapp_url = StringField(
        "Enlace de WhatsApp", 
        validators=[
            Optional(), 
            URL(message="Debe ser una URL válida"),
            Length(max=255)
        ]
    )
    
    submit = SubmitField("Crear Club")
    
    def __init__(self, edit_mode=False, *args, **kwargs):
        super(ClubForm, self).__init__(*args, **kwargs)
        if edit_mode:
            self.submit.label.text = "Guardar Cambios"
