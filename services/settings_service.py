"""
Settings Service

Questo modulo gestisce le impostazioni dell'applicazione, inclusa la configurazione
dell'API Kobold e altre preferenze utente.
"""

import os
import logging
from app import db
from models import Setting

# Impostazioni predefinite
DEFAULT_SETTINGS = {
    'kobold_api_url': 'http://localhost:5001/api',
    'use_fallback': True,
    'max_length': 1000,
    'temperature': 0.7,
    'top_p': 0.9,
    'top_k': 40
}

def init_default_settings():
    """Inizializza le impostazioni predefinite nel database."""
    try:
        # Verifica se ci sono già impostazioni nel database
        if Setting.query.count() == 0:
            # Inserisci le impostazioni predefinite
            for key, value in DEFAULT_SETTINGS.items():
                # Converti i booleani in stringa
                if isinstance(value, bool):
                    value = str(value).lower()
                
                setting = Setting(key=key, value=str(value))
                db.session.add(setting)
            
            db.session.commit()
            logging.info("Impostazioni predefinite inizializzate nel database")
    except Exception as e:
        logging.error(f"Errore nell'inizializzazione delle impostazioni predefinite: {str(e)}")
        db.session.rollback()

def get_settings():
    """
    Ottiene le impostazioni attuali dell'applicazione.
    
    Returns:
        dict: Le impostazioni correnti
    """
    try:
        # Recupera le impostazioni dal database
        settings = Setting.get_settings_dict()
        
        # Assicurati che tutte le chiavi predefinite siano presenti
        for key, value in DEFAULT_SETTINGS.items():
            if key not in settings:
                settings[key] = value
        
        return settings
    except Exception as e:
        logging.error(f"Errore durante la lettura delle impostazioni: {str(e)}")
        return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    """
    Salva le impostazioni nel database.
    
    Args:
        settings (dict): Le impostazioni da salvare
        
    Returns:
        bool: True se il salvataggio è riuscito, False altrimenti
    """
    try:
        # Mantieni solo le chiavi valide
        filtered_settings = {}
        for key in DEFAULT_SETTINGS:
            if key in settings:
                filtered_settings[key] = settings[key]
        
        # Aggiungi chiavi mancanti dai valori predefiniti
        for key, value in DEFAULT_SETTINGS.items():
            if key not in filtered_settings:
                filtered_settings[key] = value
        
        # Converti i tipi di dati
        if 'max_length' in filtered_settings:
            filtered_settings['max_length'] = int(filtered_settings['max_length'])
        
        if 'temperature' in filtered_settings:
            filtered_settings['temperature'] = float(filtered_settings['temperature'])
        
        if 'top_p' in filtered_settings:
            filtered_settings['top_p'] = float(filtered_settings['top_p'])
        
        if 'top_k' in filtered_settings:
            filtered_settings['top_k'] = int(filtered_settings['top_k'])
        
        if 'use_fallback' in filtered_settings:
            filtered_settings['use_fallback'] = filtered_settings['use_fallback'] in [True, 'true', 'True', 'on', '1', 1]
        
        # Salva le impostazioni filtrate nel database
        Setting.save_settings_dict(filtered_settings)
        
        logging.info("Impostazioni salvate con successo nel database")
        return True
    except Exception as e:
        logging.error(f"Errore durante il salvataggio delle impostazioni: {str(e)}")
        return False

def get_kobold_api_url():
    """
    Ottiene l'URL dell'API Kobold dalle impostazioni o dalla variabile d'ambiente.
    
    Returns:
        str: URL dell'API Kobold
    """
    settings = get_settings()
    return os.environ.get("KOBOLD_API_URL", settings.get('kobold_api_url', DEFAULT_SETTINGS['kobold_api_url']))

def update_from_env():
    """Aggiorna le impostazioni dalle variabili d'ambiente."""
    settings = get_settings()
    
    if "KOBOLD_API_URL" in os.environ:
        settings['kobold_api_url'] = os.environ["KOBOLD_API_URL"]
    
    save_settings(settings)
    return settings

# Non inizializzare automaticamente le impostazioni predefinite
# Le inizializzeremo in app.py dopo che il contesto dell'applicazione sarà pronto