import os
import json
import logging
import hashlib
import time
from pathlib import Path
from services.kobold_api import kobold_client

# Cartella per il caching delle richieste generate
CACHE_DIR = Path('data/ai_cache')
# Validità della cache in secondi (24 ore)
CACHE_VALIDITY = 86400

def generate_review_request(company, template, use_cache=True):
    """
    Generate a personalized review request using the local Kobold API.
    
    Args:
        company (dict): Company information including name, products, category
        template (dict): Template content to be used as base for the request
        use_cache (bool): Whether to use caching for faster responses
        
    Returns:
        str: The generated review request message
    """
    # Creiamo una chiave di cache unica basata sui dati di input
    cache_key = _generate_cache_key(company, template)
    
    # Se il caching è abilitato, verifichiamo se esiste già una risposta in cache
    if use_cache:
        cached_result = _get_cached_request(cache_key)
        if cached_result:
            logging.info(f"Usando richiesta in cache per {company['name']}")
            return cached_result
    
    try:
        logging.debug(f"Generating review request for company: {company['name']}")
        
        # Verifica che l'API Kobold sia disponibile
        start_time = time.time()
        api_available = kobold_client.health_check()
        check_time = time.time() - start_time
        
        if not api_available:
            logging.warning(f"Kobold API non è disponibile (verificato in {check_time:.2f}s), utilizzo il fallback")
            result = generate_fallback_request(company, template)
            # Non salvare in cache i risultati fallback
            return result
        
        # Prepara il prompt per Kobold
        system_prompt = "Sei C-Recenzione, un assistente professionale per la generazione di richieste di recensioni di prodotti."
        
        prompt = f"""
        Sei C-Recenzione, un sistema professionale di richiesta recensioni per prodotti.
        
        Genera una richiesta di recensione personalizzata per un'azienda basandoti sui seguenti dati:
        - Nome azienda: {company['name']}
        - Prodotti: {company.get('products', 'prodotti vari')}
        - Categoria: {company.get('category', 'generale')}
        - Sito web: {company.get('website', '')}
        
        Utilizza il seguente template come base e personalizzalo in modo appropriato:
        ---
        {template['content']}
        ---
        
        Requisiti:
        1. La richiesta deve essere professionale, convincente e in italiano corretto
        2. Personalizza il messaggio con i dettagli specifici dell'azienda
        3. Aggiungi un'introduzione formale e una chiusura cordiale
        4. Evidenzia il valore della recensione per entrambe le parti
        5. Mantieni un tono rispettoso e professionale
        6. Non includere placeholder o testo generico che deve essere sostituito
        
        Fornisci solo il testo della richiesta, senza commenti aggiuntivi.
        """
        
        # Utilizziamo il client Kobold per generare il testo
        logging.info(f"Generazione richiesta per {company['name']} tramite API Kobold")
        generation_start = time.time()
        full_prompt = f"{system_prompt}\n\n{prompt}"
        generated_text = kobold_client.generate_text(
            prompt=full_prompt,
            max_length=1000,
            temperature=0.7
        )
        generation_time = time.time() - generation_start
        
        # Pulisci la risposta da eventuali artefatti di formattazione
        generated_request = generated_text.replace(full_prompt, "").strip()
        
        logging.debug(f"Richiesta generata in {generation_time:.2f}s: {generated_request[:100]}...")
        
        # Salva in cache per usi futuri
        if use_cache and generated_request:
            _cache_request(cache_key, generated_request)
        
        return generated_request
        
    except Exception as e:
        logging.error(f"Error generating review request: {str(e)}")
        # Utilizzo del sistema di fallback se si verifica un errore
        logging.info("Utilizzo del sistema di fallback per la generazione della richiesta")
        return generate_fallback_request(company, template)

def _generate_cache_key(company, template):
    """
    Genera una chiave unica di cache basata sui dati dell'azienda e del template.
    
    Args:
        company (dict): Dati dell'azienda
        template (dict): Dati del template
        
    Returns:
        str: Chiave di cache
    """
    # Estrai i dati rilevanti
    company_data = {
        'name': company['name'],
        'products': company.get('products', ''),
        'category': company.get('category', ''),
        'website': company.get('website', '')
    }
    
    template_data = {
        'id': template['id'],
        'content': template['content']
    }
    
    # Combina i dati e crea un hash
    combined_data = json.dumps({"company": company_data, "template": template_data}, sort_keys=True)
    return hashlib.md5(combined_data.encode()).hexdigest()

def _get_cached_request(cache_key):
    """
    Recupera una richiesta dalla cache se esiste e non è scaduta.
    
    Args:
        cache_key (str): Chiave di cache
        
    Returns:
        str|None: Richiesta in cache o None se non disponibile
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{cache_key}.json"
    
    if not cache_file.exists():
        return None
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # Verifica validità cache
        if time.time() - cache_data['timestamp'] > CACHE_VALIDITY:
            logging.debug(f"Cache scaduta per {cache_key}")
            return None
        
        return cache_data['request']
    except Exception as e:
        logging.warning(f"Errore nel recupero cache: {e}")
        return None

def _cache_request(cache_key, request_text):
    """
    Salva una richiesta in cache.
    
    Args:
        cache_key (str): Chiave di cache
        request_text (str): Testo della richiesta da salvare
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{cache_key}.json"
    
    try:
        cache_data = {
            'timestamp': time.time(),
            'request': request_text
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        
        logging.debug(f"Richiesta salvata in cache: {cache_key}")
    except Exception as e:
        logging.warning(f"Errore nel salvataggio in cache: {e}")
        # Non solleviamo l'eccezione per non interrompere il flusso principale

def generate_fallback_request(company, template):
    """
    Generate a basic request using the template if AI generation fails.
    
    Args:
        company (dict): Company information
        template (dict): Template content
    
    Returns:
        str: The basic review request message
    """
    try:
        # Base template with simple replacements
        content = template['content']
        content = content.replace("[Nome Azienda]", company['name'])
        
        # Get category name
        from services.data_service import get_categories
        categories = get_categories()
        category_name = "prodotti"
        
        for category in categories:
            if category['id'] == company.get('category'):
                category_name = category['name']
                break
        
        content = content.replace("[Categoria]", category_name)
        content = content.replace("[Nome]", "Team C-Recenzione")
        
        return content
    except Exception as e:
        logging.error(f"Error generating fallback request: {str(e)}")
        return template['content']

def generate_company_suggestions(category_id, search_term=None):
    """
    Generate company suggestions for a given category using AI.
    This is a placeholder for potential future functionality.
    
    Args:
        category_id (str): The category ID to generate suggestions for
        search_term (str, optional): Optional search term to narrow results
        
    Returns:
        list: A list of suggested companies
    """
    # Questa funzionalità verrà implementata in futuro
    pass
