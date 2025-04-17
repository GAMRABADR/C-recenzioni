"""
Kobold API Client

Questo modulo fornisce un'interfaccia per interagire con l'API di Kobold.
Kobold (https://github.com/KoboldAI/KoboldAI) è un'interfaccia web per
eseguire modelli di linguaggio localmente.
"""

import os
import logging
import requests
from urllib.parse import urljoin

# Non importiamo settings_service qui per evitare importazioni circolari
# Ogni volta che avremo bisogno di impostazioni, le recupereremo direttamente

class KoboldClient:
    """Client per interagire con l'API di Kobold."""
    
    def __init__(self, base_url=None):
        """
        Inizializza il client Kobold.
        
        Args:
            base_url (str, optional): URL base dell'API Kobold.
                                     Default dalle impostazioni o localhost:5001/api
        """
        self.logger = logging.getLogger(__name__)
        
        # Valori predefiniti
        self.base_url = 'http://localhost:5001/api'
        self.temperature = 0.7
        self.max_length = 1000
        
        # Aggiorna se viene fornito un URL
        if base_url:
            self.base_url = base_url
    
    def update_settings(self, base_url=None):
        """
        Aggiorna le impostazioni del client.
        
        Args:
            base_url (str, optional): URL base dell'API Kobold.
        """
        if base_url:
            self.base_url = base_url
        else:
            # Recupera l'URL dalle impostazioni o dall'ambiente
            kobold_api_url = os.environ.get("KOBOLD_API_URL")
            if kobold_api_url:
                self.base_url = kobold_api_url
            else:
                # Tenta di recuperare dalle impostazioni
                try:
                    from flask import current_app
                    from app import app
                    
                    with app.app_context():
                        from services import settings_service
                        settings = settings_service.get_settings()
                        self.base_url = settings.get('kobold_api_url', self.base_url)
                        self.temperature = settings.get('temperature', 0.7)
                        self.max_length = settings.get('max_length', 1000)
                except Exception as e:
                    self.logger.debug(f"Non è stato possibile recuperare le impostazioni dal database: {e}")
        
        # Le impostazioni sono già state aggiornate sopra
        # Valori di default per altri parametri
        self.top_p = 0.9
        self.top_k = 40
        self.use_fallback = True
        
        self.logger.debug(f"Impostazioni Kobold aggiornate: URL={self.base_url}, temp={self.temperature}")
    
    def _make_request(self, endpoint, method="GET", data=None, timeout=30):
        """
        Effettua una richiesta all'API di Kobold.
        
        Args:
            endpoint (str): Endpoint API relativo
            method (str): Metodo HTTP (GET, POST)
            data (dict, optional): Dati da inviare (per POST)
            timeout (int): Timeout in secondi
            
        Returns:
            dict: Risposta JSON dall'API
        """
        url = urljoin(self.base_url, endpoint)
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, timeout=timeout)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, timeout=timeout)
            else:
                raise ValueError(f"Metodo non supportato: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Errore nella richiesta a Kobold API ({method} {url}): {str(e)}")
            raise
    
    def health_check(self):
        """
        Verifica lo stato dell'API Kobold.
        
        Returns:
            bool: True se l'API è disponibile
        """
        try:
            # Aggiorna le impostazioni prima del controllo
            self.update_settings()
            
            response = self._make_request("health", timeout=5)
            return response.get("status") == "ok"
        except:
            return False
    
    def generate_text(self, prompt, max_length=None, temperature=None, top_p=None, top_k=None):
        """
        Genera testo usando l'API di Kobold.
        
        Args:
            prompt (str): Prompt iniziale per la generazione
            max_length (int, optional): Lunghezza massima della generazione
            temperature (float, optional): Temperatura per la generazione (0.1-1.0)
            top_p (float, optional): Parametro top_p per la generazione
            top_k (int, optional): Parametro top_k per la generazione
            
        Returns:
            str: Testo generato
        """
        # Aggiorna le impostazioni prima della generazione
        self.update_settings()
        
        # Usa i parametri forniti o quelli predefiniti dalle impostazioni
        data = {
            "prompt": prompt,
            "max_length": max_length or self.max_length,
            "temperature": temperature or self.temperature,
            "top_p": top_p or self.top_p,
            "top_k": top_k or self.top_k,
            "rep_pen": 1.1,
            "stop_sequence": ["</s>", "User:", "System:"]
        }
        
        try:
            result = self._make_request("v1/generate", method="POST", data=data)
            return result.get("text", "").strip()
        except Exception as e:
            self.logger.error(f"Errore nella generazione del testo: {str(e)}")
            raise Exception(f"Errore nella generazione del testo: {str(e)}")
    
    def get_model_info(self):
        """
        Ottiene informazioni sul modello caricato.
        
        Returns:
            dict: Informazioni sul modello
        """
        try:
            # Aggiorna le impostazioni prima di recuperare le informazioni
            self.update_settings()
            
            return self._make_request("v1/model")
        except Exception as e:
            self.logger.error(f"Errore nell'ottenere informazioni sul modello: {str(e)}")
            return {"error": str(e)}
    
    def test_connection(self, api_url=None):
        """
        Testa la connessione a un URL specifico dell'API Kobold.
        
        Args:
            api_url (str, optional): URL da testare, usa l'URL corrente se non specificato
            
        Returns:
            dict: Risultato del test con stato e messaggio
        """
        temp_url = api_url or self.base_url
        
        try:
            # Prima verifica un semplice ping all'endpoint health
            url = urljoin(temp_url, "health")
            response = requests.get(url, timeout=5)
            
            # Se riusciamo a ottenere una risposta HTTP OK, controlliamo il contenuto
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("status") == "ok":
                        # Se l'API è sana, prova a ottenere info sul modello
                        model_url = urljoin(temp_url, "v1/model")
                        model_response = requests.get(model_url, timeout=5)
                        
                        if model_response.status_code == 200:
                            model_info = model_response.json()
                            return {
                                "success": True, 
                                "message": "Connessione riuscita e modello disponibile",
                                "model_info": model_info
                            }
                        else:
                            return {"success": True, "message": "Connessione riuscita ma info modello non disponibili"}
                    else:
                        return {"success": False, "error": "API raggiungibile ma stato non valido"}
                except ValueError:
                    return {"success": False, "error": "API ha risposto, ma il formato non è JSON valido"}
            else:
                return {"success": False, "error": f"Risposta HTTP non valida: {response.status_code}"}
                
        except requests.exceptions.ConnectionError:
            self.logger.error(f"Impossibile connettersi a {temp_url}: Connessione rifiutata")
            return {"success": False, "error": "Impossibile connettersi all'API: Connessione rifiutata"}
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout durante la connessione a {temp_url}")
            return {"success": False, "error": "Tempo scaduto durante la connessione all'API"}
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Test connessione fallito per {temp_url}: {str(e)}")
            return {"success": False, "error": str(e)}

# Istanza globale del client
kobold_client = KoboldClient()