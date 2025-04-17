import json
import os

import requests
from app import db
from flask import Blueprint, redirect, request, url_for, flash, current_app
from flask_login import login_required, login_user, logout_user
from models import User
from oauthlib.oauth2 import WebApplicationClient

# Ottenere le credenziali Google OAuth dalle variabili d'ambiente
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# URL di reindirizzamento per l'ambiente di sviluppo o produzione
DOMAIN = os.environ.get("REPLIT_DEV_DOMAIN", "")
if not DOMAIN:
    DOMAIN = os.environ.get("REPLIT_DOMAIN", "localhost:5000")

REDIRECT_URL = f'https://{DOMAIN}/google_login/callback'

# Creazione del client OAuth2 per Google
client = WebApplicationClient(GOOGLE_CLIENT_ID) if GOOGLE_CLIENT_ID else None

# Creazione del blueprint Flask per l'autenticazione Google
google_auth = Blueprint("google_auth", __name__)

@google_auth.route("/google_login")
def login():
    """Inizia il flusso di autenticazione OAuth con Google."""
    if not client:
        flash("L'autenticazione Google non è configurata correttamente.", "warning")
        return redirect(url_for('login'))
    
    # Ottieni la configurazione del provider di autenticazione Google
    try:
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]
        
        # Prepara l'URI di autorizzazione
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            # Sostituisci http:// con https:// se necessario
            redirect_uri=request.base_url.replace("http://", "https://") + "/callback",
            scope=["openid", "email", "profile"],
        )
        return redirect(request_uri)
    except Exception as e:
        current_app.logger.error(f"Errore durante l'inizializzazione OAuth: {e}")
        flash("Si è verificato un errore durante la connessione a Google.", "danger")
        return redirect(url_for('login'))

@google_auth.route("/google_login/callback")
def callback():
    """Callback per l'autenticazione OAuth di Google."""
    if not client:
        flash("L'autenticazione Google non è configurata correttamente.", "warning")
        return redirect(url_for('login'))
    
    try:
        # Ottieni il codice di autorizzazione
        code = request.args.get("code")
        if not code:
            flash("Autenticazione fallita: codice di autorizzazione mancante.", "danger")
            return redirect(url_for('login'))
        
        # Ottieni l'endpoint del token
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        token_endpoint = google_provider_cfg["token_endpoint"]
        
        # Prepara la richiesta del token
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            # Sostituisci http:// con https:// se necessario
            authorization_response=request.url.replace("http://", "https://"),
            redirect_url=request.base_url.replace("http://", "https://"),
            code=code,
        )
        
        # Invia la richiesta al server del token
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )
        
        # Analizza la risposta del token
        client.parse_request_body_response(json.dumps(token_response.json()))
        
        # Ottieni le informazioni dell'utente
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)
        
        # Verifica che l'email sia verificata
        userinfo = userinfo_response.json()
        if userinfo.get("email_verified"):
            users_email = userinfo["email"]
            users_name = userinfo.get("given_name", "")
            users_surname = userinfo.get("family_name", "")
            
            # Cerca l'utente nel database o creane uno nuovo
            user = User.query.filter_by(email=users_email).first()
            if not user:
                # Crea un nuovo utente
                user = User(
                    username=users_name.lower() + "." + users_surname.lower() if users_surname else users_name.lower(),
                    email=users_email,
                    first_name=users_name,
                    last_name=users_surname
                )
                # Genera una password casuale sicura che l'utente non utilizzerà
                import secrets
                random_password = secrets.token_urlsafe(16)
                user.set_password(random_password)
                
                db.session.add(user)
                db.session.commit()
                flash("Account creato con successo tramite Google!", "success")
            else:
                flash("Accesso effettuato con successo!", "success")
            
            # Effettua il login dell'utente
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash("L'email non è verificata da Google.", "danger")
            return redirect(url_for('login'))
    except Exception as e:
        current_app.logger.error(f"Errore durante il callback OAuth: {e}")
        flash("Si è verificato un errore durante l'autenticazione con Google.", "danger")
        return redirect(url_for('login'))

@google_auth.route("/logout")
@login_required
def logout():
    """Effettua il logout dell'utente."""
    logout_user()
    flash("Sei stato disconnesso.", "info")
    return redirect(url_for('index'))