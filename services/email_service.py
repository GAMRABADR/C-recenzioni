import os
import logging
import smtplib
import json
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from pathlib import Path

# Cartella per salvare le email in modalità locale
LOCAL_EMAIL_DIR = Path('data/local_emails')

def send_email(recipient_email, subject, message_body):
    """
    Send an email using Mailtrap API, SMTP or save locally in development mode.
    
    Args:
        recipient_email (str): The recipient's email address
        subject (str): The email subject
        message_body (str): The email body content
        
    Returns:
        dict: Result of the sending operation including status and timestamp
    """
    timestamp = datetime.now().isoformat()
    
    # Configurazione email
    sender_email = os.environ.get("EMAIL_SENDER", "c-recenzione@example.com")
    sender_name = os.environ.get("EMAIL_SENDER_NAME", "C-Recenzione")
    
    # Determina la modalità di invio
    use_local_storage = os.environ.get("EMAIL_LOCAL_STORAGE", "true").lower() == "true"
    use_test_mode = os.environ.get("EMAIL_TEST_MODE", "false").lower() == "true"
    use_mailtrap = os.environ.get("USE_MAILTRAP", "true").lower() == "true"
    
    try:
        # Se è richiesto l'uso di Mailtrap e l'API token è disponibile
        if use_mailtrap and os.environ.get("MAILTRAP_API_TOKEN"):
            return send_via_mailtrap(sender_email, sender_name, recipient_email, subject, message_body, timestamp)
        
        # Se è richiesto il salvataggio locale o attiva la modalità test
        if use_local_storage or use_test_mode:
            return save_email_locally(recipient_email, subject, message_body, timestamp)
        
        # Altrimenti tenta di inviare tramite SMTP
        # Creazione messaggio SMTP
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message_body, 'html'))
        
        return send_via_smtp(msg, recipient_email, timestamp)
        
    except Exception as e:
        logging.error(f"Errore nell'invio dell'email: {str(e)}")
        
        # In caso di errore, fallback al salvataggio locale
        if use_local_storage:
            logging.info("Fallback al salvataggio locale dell'email")
            return save_email_locally(recipient_email, subject, message_body, timestamp)
        
        # Se il fallback non è abilitato, alza l'eccezione
        raise Exception(f"Errore nell'invio dell'email: {str(e)}")

def send_via_mailtrap(sender_email, sender_name, recipient_email, subject, message_body, timestamp):
    """
    Invia un'email tramite Mailtrap API.
    
    Args:
        sender_email: Email del mittente
        sender_name: Nome del mittente
        recipient_email: Email del destinatario
        subject: Oggetto dell'email
        message_body: Corpo dell'email in HTML
        timestamp: Timestamp dell'operazione
        
    Returns:
        dict: Risultato dell'operazione
    """
    mailtrap_token = os.environ.get("MAILTRAP_API_TOKEN")
    mailtrap_inbox_id = os.environ.get("MAILTRAP_INBOX_ID", "3626747")  # ID della inbox Mailtrap
    
    if not mailtrap_token:
        raise ValueError("Mailtrap API token non configurato")
    
    logging.debug(f"Invio email tramite Mailtrap a {recipient_email} con oggetto: {subject}")
    
    url = f"https://sandbox.api.mailtrap.io/api/send/{mailtrap_inbox_id}"
    headers = {
        "Authorization": f"Bearer {mailtrap_token}",
        "Content-Type": "application/json"
    }
    
    # Preparazione del payload
    payload = {
        "from": {
            "email": sender_email,
            "name": sender_name
        },
        "to": [
            {
                "email": recipient_email
            }
        ],
        "subject": subject,
        "html": message_body,
        "text": "Questo è un messaggio generato da C-Recenzione.",
        "category": "C-Recenzione"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Solleva un'eccezione se la risposta non è 2xx
        
        result = response.json()
        logging.info(f"Email inviata tramite Mailtrap con successo a {recipient_email} (status: {response.status_code})")
        
        return {
            "status": "delivered",
            "date": timestamp,
            "mailtrap_id": result.get("id", "unknown"),
            "mailtrap_status": response.status_code
        }
    except Exception as e:
        logging.error(f"Errore nell'invio dell'email tramite Mailtrap: {str(e)}")
        raise

def send_via_smtp(msg, recipient_email, timestamp):
    """
    Invia un'email tramite SMTP.
    
    Args:
        msg: Messaggio email da inviare
        recipient_email: Email del destinatario
        timestamp: Timestamp dell'operazione
        
    Returns:
        dict: Risultato dell'operazione
    """
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.example.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_username = os.environ.get("SMTP_USERNAME", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    
    logging.debug(f"Invio email a {recipient_email} con oggetto: {msg['Subject']}")
    
    # Connect to server and send email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()  # Secure the connection
        
        # Login if credentials are provided
        if smtp_username and smtp_password:
            server.login(smtp_username, smtp_password)
        
        # Send email
        server.send_message(msg)
        logging.info(f"Email inviata con successo a {recipient_email}")
        
        return {
            "status": "delivered",
            "date": timestamp
        }

def save_email_locally(recipient_email, subject, message_body, timestamp):
    """
    Salva l'email localmente per lo sviluppo/testing.
    
    Args:
        recipient_email: Email del destinatario
        subject: Oggetto dell'email
        message_body: Corpo dell'email
        timestamp: Timestamp dell'operazione
        
    Returns:
        dict: Risultato dell'operazione
    """
    # Crea la directory se non esiste
    LOCAL_EMAIL_DIR.mkdir(parents=True, exist_ok=True)
    
    # Genera un nome file univoco
    filename = LOCAL_EMAIL_DIR / f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{recipient_email.replace('@', '_at_')}.json"
    
    # Salva l'email come JSON
    email_data = {
        "to": recipient_email,
        "subject": subject,
        "body": message_body,
        "date": timestamp
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(email_data, f, indent=2, ensure_ascii=False)
    
    logging.info(f"Email salvata localmente: {filename}")
    
    return {
        "status": "delivered",
        "date": timestamp,
        "local_file": str(filename)
    }