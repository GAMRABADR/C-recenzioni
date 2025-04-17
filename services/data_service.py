"""
Data Service - Versione Database

Questo modulo gestisce l'accesso ai dati dell'applicazione tramite il database PostgreSQL.
"""

import logging
from datetime import datetime
from app import db
from models import Category, Company, Template, Request

# Data function wrapper for ensuring session cleanup
def db_operation(func):
    """Decorator per gestire le operazioni sul database in modo sicuro."""
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            db.session.rollback()
            logging.error(f"Errore nell'operazione sul database: {str(e)}")
            raise
    return wrapper

# CRUD operations for categories
@db_operation
def get_categories():
    """Get all product categories."""
    try:
        categories = Category.query.all()
        return [c.to_dict() for c in categories]
    except Exception as e:
        logging.error(f"Error reading categories: {str(e)}")
        return []

@db_operation
def add_category(category_data):
    """Add a new product category."""
    try:
        category = Category(
            name=category_data.get('name', ''),
            description=category_data.get('description', '')
        )
        db.session.add(category)
        db.session.commit()
        return category.to_dict()
    except Exception as e:
        logging.error(f"Error adding category: {str(e)}")
        raise

# CRUD operations for companies
@db_operation
def get_companies():
    """Get all companies."""
    try:
        companies = Company.query.all()
        return [c.to_dict() for c in companies]
    except Exception as e:
        logging.error(f"Error reading companies: {str(e)}")
        return []

@db_operation
def get_company_by_id(company_id):
    """Get a company by ID."""
    try:
        company = Company.query.get(company_id)
        return company.to_dict() if company else None
    except Exception as e:
        logging.error(f"Error retrieving company {company_id}: {str(e)}")
        return None

@db_operation
def add_company(company_data):
    """Add a new company."""
    try:
        company = Company(
            name=company_data.get('name', ''),
            email=company_data.get('email', ''),
            website=company_data.get('website', ''),
            products=company_data.get('products', ''),
            notes=company_data.get('notes', ''),
            category_id=company_data.get('category', '')
        )
        db.session.add(company)
        db.session.commit()
        return company.to_dict()
    except Exception as e:
        logging.error(f"Error adding company: {str(e)}")
        raise

@db_operation
def update_company(updated_company_data):
    """Update an existing company."""
    try:
        company = Company.query.get(updated_company_data.get('id'))
        if not company:
            raise ValueError(f"Azienda non trovata con ID: {updated_company_data.get('id')}")
        
        # Aggiorna i campi
        company.name = updated_company_data.get('name', company.name)
        company.email = updated_company_data.get('email', company.email)
        company.website = updated_company_data.get('website', company.website)
        company.products = updated_company_data.get('products', company.products)
        company.notes = updated_company_data.get('notes', company.notes)
        company.category_id = updated_company_data.get('category', company.category_id)
        
        db.session.commit()
        return company.to_dict()
    except Exception as e:
        logging.error(f"Error updating company: {str(e)}")
        raise

@db_operation
def delete_company(company_id):
    """Delete a company by ID."""
    try:
        company = Company.query.get(company_id)
        if company:
            db.session.delete(company)
            db.session.commit()
        return True
    except Exception as e:
        logging.error(f"Error deleting company {company_id}: {str(e)}")
        raise

# CRUD operations for templates
@db_operation
def get_templates():
    """Get all templates."""
    try:
        templates = Template.query.all()
        return [t.to_dict() for t in templates]
    except Exception as e:
        logging.error(f"Error reading templates: {str(e)}")
        return []

@db_operation
def get_template_by_id(template_id):
    """Get a template by ID."""
    try:
        template = Template.query.get(template_id)
        return template.to_dict() if template else None
    except Exception as e:
        logging.error(f"Error retrieving template {template_id}: {str(e)}")
        return None

@db_operation
def add_template(template_data):
    """Add a new template."""
    try:
        template = Template(
            name=template_data.get('name', ''),
            content=template_data.get('content', ''),
            category_id=template_data.get('category', '')
        )
        db.session.add(template)
        db.session.commit()
        return template.to_dict()
    except Exception as e:
        logging.error(f"Error adding template: {str(e)}")
        raise

@db_operation
def update_template(updated_template_data):
    """Update an existing template."""
    try:
        template = Template.query.get(updated_template_data.get('id'))
        if not template:
            raise ValueError(f"Template non trovato con ID: {updated_template_data.get('id')}")
        
        # Aggiorna i campi
        template.name = updated_template_data.get('name', template.name)
        template.content = updated_template_data.get('content', template.content)
        template.category_id = updated_template_data.get('category', template.category_id)
        
        db.session.commit()
        return template.to_dict()
    except Exception as e:
        logging.error(f"Error updating template: {str(e)}")
        raise

@db_operation
def delete_template(template_id):
    """Delete a template by ID."""
    try:
        template = Template.query.get(template_id)
        if template:
            db.session.delete(template)
            db.session.commit()
        return True
    except Exception as e:
        logging.error(f"Error deleting template {template_id}: {str(e)}")
        raise

# CRUD operations for review requests
@db_operation
def get_requests():
    """Get all review requests."""
    try:
        requests = Request.query.all()
        return [r.to_dict() for r in requests]
    except Exception as e:
        logging.error(f"Error reading requests: {str(e)}")
        return []

@db_operation
def save_request(request_data):
    """Save a new review request."""
    try:
        # Converti la data da string ISO a datetime se necessario
        date_sent = request_data.get('date_sent')
        if isinstance(date_sent, str):
            date_sent = datetime.fromisoformat(date_sent.replace('Z', '+00:00'))
        else:
            date_sent = datetime.utcnow()
        
        request_obj = Request(
            company_id=request_data.get('company_id'),
            template_id=request_data.get('template_id'),
            subject=request_data.get('subject', 'Richiesta di recensione'),
            message=request_data.get('message', ''),
            date_sent=date_sent,
            status=request_data.get('status', 'pending'),
            opened=request_data.get('opened', False),
            responded=request_data.get('responded', False),
            opened_count=request_data.get('opened_count', 0)
        )
        
        db.session.add(request_obj)
        db.session.commit()
        return request_obj.to_dict()
    except Exception as e:
        logging.error(f"Error saving request: {str(e)}")
        raise

@db_operation
def update_request_status(request_id, status_updates):
    """Update the status of a review request."""
    try:
        request_obj = Request.query.get(request_id)
        if not request_obj:
            raise ValueError(f"Richiesta non trovata con ID: {request_id}")
        
        # Aggiorna i campi
        if 'status' in status_updates:
            request_obj.status = status_updates['status']
        
        if 'opened' in status_updates:
            request_obj.opened = status_updates['opened']
            if status_updates['opened'] and not request_obj.date_opened:
                request_obj.date_opened = datetime.utcnow()
            request_obj.opened_count += 1
        
        if 'responded' in status_updates:
            request_obj.responded = status_updates['responded']
            if status_updates['responded'] and not request_obj.date_responded:
                request_obj.date_responded = datetime.utcnow()
        
        db.session.commit()
        return request_obj.to_dict()
    except Exception as e:
        logging.error(f"Error updating request status: {str(e)}")
        raise

# Funzione per migrare i dati dai file JSON al database (per compatibilità)
def migrate_json_to_db(json_data, model_class, map_func):
    """Migra dati da JSON al database."""
    try:
        if not json_data:
            return
            
        for item in json_data:
            db_obj = map_func(item)
            db.session.add(db_obj)
        
        db.session.commit()
        logging.info(f"Migrati {len(json_data)} elementi nel database")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Errore nella migrazione dei dati: {str(e)}")
        raise
