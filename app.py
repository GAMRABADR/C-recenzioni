import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase

# Carica variabili d'ambiente dal file .env se presente
env_path = Path('.') / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"Variabili d'ambiente caricate da {env_path}")

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create the Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "placeholder-secret-key")

# Configure the SQLAlchemy database
database_url = os.environ.get("DATABASE_URL")
if database_url:
    # Assicurati che l'URL del database sia formattato correttamente
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    # Se DATABASE_URL non è impostato, usa un database SQLite in memoria per test
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///c_recenzione.db"

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configurazione Firebase (se disponibile)
app.config['FIREBASE_API_KEY'] = os.environ.get('FIREBASE_API_KEY')
app.config['FIREBASE_PROJECT_ID'] = os.environ.get('FIREBASE_PROJECT_ID')
app.config['FIREBASE_APP_ID'] = os.environ.get('FIREBASE_APP_ID')

# Initialize the database with the app
db.init_app(app)

# Inizializza Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Nome della funzione per il login
login_manager.login_message = 'Accedi per visualizzare questa pagina.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(user_id)

# Create database tables if they don't exist
with app.app_context():
    # Import models before creating tables
    from models import User, Category, Company, Template, Request, Setting
    db.create_all()
    
    # Inizializza le impostazioni predefinite nel database
    from services.settings_service import init_default_settings
    init_default_settings()
    
    # Verifica se ci sono dati nelle tabelle principali
    if Category.query.count() == 0:
        # Aggiungi rotte di inizializzazione e accesso all'endpoint /init_db
        pass

# Import models e routes
# Importante: le importazioni devono essere qui per evitare importazioni circolari
from models import *
from routes import *

# Importa e registra il blueprint per l'autenticazione Google
try:
    from google_auth import google_auth
    app.register_blueprint(google_auth)
    print("Blueprint di autenticazione Google registrato")
except ImportError as e:
    print(f"Impossibile caricare il blueprint di autenticazione Google: {e}")
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)