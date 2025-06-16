from flask_wtf import FlaskForm
from wtforms import StringField, FileField, SubmitField, HiddenField
from wtforms.validators import Optional


class FeedImageForm(FlaskForm):
    form_type = HiddenField(default="image")
    title = StringField("Título o descripción", validators=[Optional()])
    image = FileField("Imagen", validators=[Optional()])
    submit = SubmitField("Compartir")
