from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Optional


class FeedNoteForm(FlaskForm):
    form_type = HiddenField(default="note")
    title = StringField("Título", validators=[DataRequired()])
    summary = TextAreaField("Resumen", validators=[Optional()])
    tags = StringField("Etiquetas", validators=[Optional()])
    file = FileField("Archivo PDF", validators=[Optional()])
    submit = SubmitField("Publicar")
