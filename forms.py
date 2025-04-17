from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional, NumberRange
from models import User

class RegistrationForm(FlaskForm):
    """Form per la registrazione di un nuovo utente."""
    username = StringField('Nome utente', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Ripeti Password', validators=[DataRequired(), EqualTo('password')])
    first_name = StringField('Nome', validators=[Optional(), Length(max=64)])
    last_name = StringField('Cognome', validators=[Optional(), Length(max=64)])
    submit = SubmitField('Registrati')
    
    def validate_username(self, username):
        """Verifica che l'username non sia già in uso."""
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Questo nome utente è già in uso. Scegline un altro.')
    
    def validate_email(self, email):
        """Verifica che l'email non sia già in uso."""
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Questa email è già registrata. Usa un\'altra email o accedi.')

class LoginForm(FlaskForm):
    """Form per il login."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Ricordami')
    submit = SubmitField('Accedi')

class EmailSettingsForm(FlaskForm):
    """Form per le impostazioni email dell'utente."""
    smtp_server = StringField('Server SMTP', validators=[DataRequired(), Length(max=128)])
    smtp_port = IntegerField('Porta SMTP', validators=[DataRequired(), NumberRange(min=1, max=65535)])
    smtp_username = StringField('Username SMTP', validators=[DataRequired(), Length(max=128)])
    smtp_password = PasswordField('Password SMTP', validators=[DataRequired(), Length(max=128)])
    smtp_use_tls = BooleanField('Usa TLS', default=True)
    email_sender_name = StringField('Nome mittente', validators=[DataRequired(), Length(max=128)])
    submit = SubmitField('Salva impostazioni')