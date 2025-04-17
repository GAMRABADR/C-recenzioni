from datetime import datetime
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db

class Category(db.Model):
    """Categoria di prodotti."""
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relazioni
    companies = db.relationship('Company', backref='category_rel', lazy=True)
    templates = db.relationship('Template', backref='category_rel', lazy=True)
    
    def to_dict(self):
        """Converte l'oggetto in un dizionario."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Company(db.Model):
    """Azienda da contattare per recensioni."""
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    website = db.Column(db.String(255), nullable=True)
    products = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.String(36), db.ForeignKey('category.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relazioni
    requests = db.relationship('Request', backref='company', lazy=True)
    
    def to_dict(self):
        """Converte l'oggetto in un dizionario."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'website': self.website,
            'products': self.products,
            'notes': self.notes,
            'category': self.category_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Template(db.Model):
    """Template per le richieste di recensione."""
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.String(36), db.ForeignKey('category.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Converte l'oggetto in un dizionario."""
        return {
            'id': self.id,
            'name': self.name,
            'content': self.content,
            'category': self.category_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Request(db.Model):
    """Richiesta di recensione inviata."""
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = db.Column(db.String(36), db.ForeignKey('company.id'), nullable=False)
    template_id = db.Column(db.String(36), db.ForeignKey('template.id'), nullable=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=True)
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date_sent = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='pending')  # pending, delivered, failed
    opened = db.Column(db.Boolean, default=False)
    date_opened = db.Column(db.DateTime, nullable=True)
    responded = db.Column(db.Boolean, default=False)
    date_responded = db.Column(db.DateTime, nullable=True)
    opened_count = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        """Converte l'oggetto in un dizionario."""
        return {
            'id': self.id,
            'company_id': self.company_id,
            'company_name': self.company.name if self.company else None,
            'category': self.company.category_id if self.company else None,
            'template_id': self.template_id,
            'email': self.company.email if self.company else None,
            'subject': self.subject,
            'message': self.message,
            'date_sent': self.date_sent.isoformat() if self.date_sent else None,
            'status': self.status,
            'opened': self.opened,
            'date_opened': self.date_opened.isoformat() if self.date_opened else None,
            'responded': self.responded,
            'date_responded': self.date_responded.isoformat() if self.date_responded else None,
            'opened_count': self.opened_count
        }

class User(UserMixin, db.Model):
    """Utente del sistema."""
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64), nullable=True)
    last_name = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Impostazioni email
    smtp_server = db.Column(db.String(128), nullable=True)
    smtp_port = db.Column(db.Integer, nullable=True)
    smtp_username = db.Column(db.String(128), nullable=True)
    smtp_password = db.Column(db.String(256), nullable=True)
    smtp_use_tls = db.Column(db.Boolean, default=True)
    email_sender_name = db.Column(db.String(128), nullable=True)
    
    # Relazioni
    requests = db.relationship('Request', backref='user', lazy=True)
    companies = db.relationship('Company', backref='user', lazy=True)
    templates = db.relationship('Template', backref='user', lazy=True)
    
    def set_password(self, password):
        """Imposta l'hash della password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica la password."""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Converte l'oggetto in un dizionario."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'has_smtp_config': bool(self.smtp_server and self.smtp_username)
        }

class Setting(db.Model):
    """Impostazioni dell'applicazione."""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_settings_dict(cls):
        """Recupera tutte le impostazioni come dizionario chiave-valore."""
        settings = cls.query.all()
        settings_dict = {}
        
        for setting in settings:
            # Converti in booleano o numeri se necessario
            if setting.value == 'true':
                settings_dict[setting.key] = True
            elif setting.value == 'false':
                settings_dict[setting.key] = False
            elif setting.value and setting.value.isdigit():
                settings_dict[setting.key] = int(setting.value)
            elif setting.value and setting.value.replace('.', '', 1).isdigit():
                settings_dict[setting.key] = float(setting.value)
            else:
                settings_dict[setting.key] = setting.value
        
        return settings_dict
    
    @classmethod
    def save_settings_dict(cls, settings_dict):
        """Salva un dizionario di impostazioni nel database."""
        for key, value in settings_dict.items():
            # Converti in stringa per il salvataggio
            if isinstance(value, bool):
                str_value = str(value).lower()
            else:
                str_value = str(value) if value is not None else None
            
            # Cerca l'impostazione esistente o ne crea una nuova
            setting = cls.query.filter_by(key=key).first()
            if setting:
                setting.value = str_value
            else:
                new_setting = cls(key=key, value=str_value)
                db.session.add(new_setting)
        
        db.session.commit()
        return True
