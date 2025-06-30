from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional


class ClubForm(FlaskForm):
    name = StringField("Nombre", validators=[DataRequired()])
    career = StringField("Carrera", validators=[DataRequired()])
    description = TextAreaField("Descripción", validators=[Optional()])
    submit = SubmitField("Crear Club")
