import os
import logging
import datetime
import json
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from app import app, db
from models import Category, Company, Template, Request, Setting, User
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse
from forms import RegistrationForm, LoginForm, EmailSettingsForm
from services.ai_service import generate_review_request
from services.email_service import send_email
from services.kobold_api import kobold_client

# Routes di autenticazione
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Email o password non validi', 'danger')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('dashboard')
        return redirect(next_page)
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registrazione completata con successo! Ora puoi accedere.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('Sei stato disconnesso.', 'info')
    return redirect(url_for('index'))

# Routes principali
@app.route('/')
def index():
    categories = Category.query.all()
    return render_template('index.html', categories=[c.to_dict() for c in categories])

@app.route('/companies')
def companies():
    companies_data = Company.query.all()
    categories = Category.query.all()
    return render_template('companies.html', 
                          companies=[c.to_dict() for c in companies_data], 
                          categories=[c.to_dict() for c in categories])

@app.route('/companies/add', methods=['POST'])
def add_company_route():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        category_id = request.form.get('category')
        website = request.form.get('website')
        products = request.form.get('products')
        
        if not all([name, email, category_id]):
            flash('Nome, email e categoria sono obbligatori', 'danger')
            return redirect(url_for('companies'))
        
        # Verifica che la categoria esista
        category = Category.query.get(category_id)
        if not category:
            flash('Categoria non valida', 'danger')
            return redirect(url_for('companies'))
        
        company = Company(
            name=name,
            email=email,
            category_id=category_id,
            website=website or "",
            products=products or ""
        )
        
        db.session.add(company)
        db.session.commit()
        flash('Azienda aggiunta con successo', 'success')
    
    return redirect(url_for('companies'))

@app.route('/companies/edit/<company_id>', methods=['POST'])
def edit_company(company_id):
    if request.method == 'POST':
        company = Company.query.get(company_id)
        
        if not company:
            flash('Azienda non trovata', 'danger')
            return redirect(url_for('companies'))
        
        name = request.form.get('name')
        email = request.form.get('email')
        category_id = request.form.get('category')
        website = request.form.get('website')
        products = request.form.get('products')
        
        if not all([name, email, category_id]):
            flash('Nome, email e categoria sono obbligatori', 'danger')
            return redirect(url_for('companies'))
        
        # Update company data
        company.name = name
        company.email = email
        company.category_id = category_id
        company.website = website or ""
        company.products = products or ""
        
        db.session.commit()
        flash('Azienda aggiornata con successo', 'success')
    
    return redirect(url_for('companies'))

@app.route('/companies/delete/<company_id>', methods=['POST'])
def delete_company_route(company_id):
    company = Company.query.get(company_id)
    
    if company:
        db.session.delete(company)
        db.session.commit()
        flash('Azienda eliminata con successo', 'success')
    else:
        flash('Azienda non trovata', 'danger')
    
    return redirect(url_for('companies'))

@app.route('/templates')
def templates():
    templates_data = Template.query.all()
    categories = Category.query.all()
    return render_template('templates.html', 
                          templates=[t.to_dict() for t in templates_data], 
                          categories=[c.to_dict() for c in categories])

@app.route('/templates/add', methods=['POST'])
def add_template_route():
    if request.method == 'POST':
        name = request.form.get('name')
        category_id = request.form.get('category')
        content = request.form.get('content')
        
        if not all([name, category_id, content]):
            flash('Nome, categoria e contenuto sono obbligatori', 'danger')
            return redirect(url_for('templates'))
        
        # Verifica che la categoria esista
        category = Category.query.get(category_id)
        if not category:
            flash('Categoria non valida', 'danger')
            return redirect(url_for('templates'))
        
        template = Template(
            name=name,
            category_id=category_id,
            content=content
        )
        
        db.session.add(template)
        db.session.commit()
        flash('Template aggiunto con successo', 'success')
    
    return redirect(url_for('templates'))

@app.route('/templates/edit/<template_id>', methods=['POST'])
def edit_template(template_id):
    if request.method == 'POST':
        template = Template.query.get(template_id)
        
        if not template:
            flash('Template non trovato', 'danger')
            return redirect(url_for('templates'))
        
        name = request.form.get('name')
        category_id = request.form.get('category')
        content = request.form.get('content')
        
        if not all([name, category_id, content]):
            flash('Nome, categoria e contenuto sono obbligatori', 'danger')
            return redirect(url_for('templates'))
        
        # Update template data
        template.name = name
        template.category_id = category_id
        template.content = content
        
        db.session.commit()
        flash('Template aggiornato con successo', 'success')
    
    return redirect(url_for('templates'))

@app.route('/templates/delete/<template_id>', methods=['POST'])
def delete_template_route(template_id):
    template = Template.query.get(template_id)
    
    if template:
        db.session.delete(template)
        db.session.commit()
        flash('Template eliminato con successo', 'success')
    else:
        flash('Template non trovato', 'danger')
    
    return redirect(url_for('templates'))

@app.route('/dashboard')
def dashboard():
    companies_data = Company.query.all()
    templates_data = Template.query.all()
    categories = Category.query.all()
    requests_data = Request.query.all()
    
    return render_template(
        'dashboard.html', 
        companies=[c.to_dict() for c in companies_data], 
        templates=[t.to_dict() for t in templates_data], 
        categories=[c.to_dict() for c in categories],
        requests=[r.to_dict() for r in requests_data]
    )

@app.route('/reports')
def reports():
    requests_data = Request.query.all()
    categories = Category.query.all()
    
    # Calculate statistics
    requests_list = [r.to_dict() for r in requests_data]
    total_requests = len(requests_list)
    delivered = sum(1 for r in requests_list if r.get('status') == 'delivered')
    opened = sum(1 for r in requests_list if r.get('opened', False))
    responded = sum(1 for r in requests_list if r.get('responded', False))
    
    stats = {
        'total': total_requests,
        'delivered': delivered,
        'delivery_rate': round((delivered / total_requests * 100) if total_requests > 0 else 0, 1),
        'opened': opened,
        'open_rate': round((opened / delivered * 100) if delivered > 0 else 0, 1),
        'responded': responded,
        'response_rate': round((responded / opened * 100) if opened > 0 else 0, 1)
    }
    
    # Group requests by category
    category_stats = {}
    for category in categories:
        category_dict = category.to_dict()
        category_requests = [r for r in requests_list if r.get('category') == category_dict['id']]
        if category_requests:
            cat_delivered = sum(1 for r in category_requests if r.get('status') == 'delivered')
            cat_opened = sum(1 for r in category_requests if r.get('opened', False))
            cat_responded = sum(1 for r in category_requests if r.get('responded', False))
            
            category_stats[category_dict['name']] = {
                'total': len(category_requests),
                'delivered': cat_delivered,
                'opened': cat_opened,
                'responded': cat_responded
            }
    
    return render_template('reports.html', requests=requests_list, stats=stats, category_stats=category_stats)

@app.route('/generate_request', methods=['POST'])
def generate_request_route():
    data = request.json
    company_id = data.get('company_id')
    template_id = data.get('template_id')
    
    if not company_id or not template_id:
        return jsonify({'error': 'Dati mancanti'}), 400
    
    company = Company.query.get(company_id)
    template = Template.query.get(template_id)
    
    if not company or not template:
        return jsonify({'error': 'Azienda o template non trovato'}), 404
    
    try:
        # Generate the request using AI
        ai_generated_request = generate_review_request(company.to_dict(), template.to_dict())
        
        return jsonify({
            'message': ai_generated_request,
            'company': company.to_dict()
        })
    except Exception as e:
        logging.error(f"Error generating request: {str(e)}")
        return jsonify({'error': f'Errore durante la generazione della richiesta: {str(e)}'}), 500

@app.route('/send_request', methods=['POST'])
def send_request_route():
    data = request.json
    company_id = data.get('company_id')
    template_id = data.get('template_id', None)
    message = data.get('message')
    subject = data.get('subject', 'Richiesta di recensione prodotto')
    
    if not company_id or not message:
        return jsonify({'error': 'Dati mancanti'}), 400
    
    company = Company.query.get(company_id)
    
    if not company:
        return jsonify({'error': 'Azienda non trovata'}), 404
    
    try:
        # Send email
        send_result = send_email(company.email, subject, message)
        
        if send_result:
            # Save the request to track it
            request_obj = Request(
                company_id=company_id,
                template_id=template_id,
                subject=subject,
                message=message,
                date_sent=datetime.datetime.fromisoformat(send_result['date']) if isinstance(send_result['date'], str) else datetime.datetime.utcnow(),
                status='delivered',
                opened=False,
                responded=False
            )
            
            db.session.add(request_obj)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Richiesta inviata con successo'})
        else:
            return jsonify({'error': 'Errore durante l\'invio dell\'email'}), 500
    except Exception as e:
        logging.error(f"Error sending email: {str(e)}")
        return jsonify({'error': f'Errore durante l\'invio dell\'email: {str(e)}'}), 500

@app.route('/settings')
def settings():
    """Visualizza la pagina delle impostazioni."""
    settings_data = Setting.get_settings_dict()
    return render_template('settings.html', current_settings=settings_data)

@app.route('/settings/save', methods=['POST'])
def save_settings_route():
    """Salva le impostazioni dell'applicazione."""
    if request.method == 'POST':
        settings_data = {
            'kobold_api_url': request.form.get('kobold_api_url'),
            'use_fallback': 'use_fallback' in request.form,
            'max_length': request.form.get('max_length', 1000),
            'temperature': request.form.get('temperature', 0.7)
        }
        
        if Setting.save_settings_dict(settings_data):
            # Aggiorna il client Kobold con le nuove impostazioni
            kobold_client.update_settings()
            flash('Impostazioni salvate con successo', 'success')
        else:
            flash('Errore durante il salvataggio delle impostazioni', 'danger')
    
    return redirect(url_for('settings'))

@app.route('/test_kobold_connection', methods=['POST'])
def test_kobold_connection():
    """Test della connessione all'API Kobold."""
    data = request.json
    api_url = data.get('api_url')
    
    try:
        # Test della connessione
        result = kobold_client.test_connection(api_url)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Errore nel test della connessione Kobold: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_kobold_model_info', methods=['POST'])
def get_kobold_model_info():
    """Ottiene informazioni sul modello Kobold."""
    data = request.json
    api_url = data.get('api_url')
    
    try:
        # Usa temporaneamente l'URL specificato
        if api_url:
            kobold_client.update_settings(api_url)
        
        # Ottieni informazioni sul modello
        model_info = kobold_client.get_model_info()
        
        # Ripristina le impostazioni originali se è stato specificato un URL temporaneo
        if api_url:
            kobold_client.update_settings()
        
        return jsonify({'success': True, 'model_info': model_info})
    except Exception as e:
        logging.error(f"Errore nel recupero delle informazioni sul modello Kobold: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/emails')
def show_local_emails():
    """Visualizza le email salvate localmente per debugging."""
    from services.email_service import LOCAL_EMAIL_DIR
    from pathlib import Path
    import json
    
    # Verifica se la modalità di debug è attiva
    if not app.debug and os.environ.get("SHOW_EMAILS", "false").lower() != "true":
        flash('Questa funzionalità è disponibile solo in modalità debug', 'warning')
        return redirect(url_for('index'))
    
    try:
        # Crea la directory se non esiste
        LOCAL_EMAIL_DIR.mkdir(parents=True, exist_ok=True)
        
        # Leggi le email salvate
        emails = []
        for email_file in LOCAL_EMAIL_DIR.glob('*.json'):
            try:
                with open(email_file, 'r', encoding='utf-8') as f:
                    email_data = json.load(f)
                    
                email_data['filename'] = email_file.name
                email_data['created_at'] = datetime.datetime.fromtimestamp(
                    email_file.stat().st_mtime
                ).strftime('%Y-%m-%d %H:%M:%S')
                
                emails.append(email_data)
            except Exception as e:
                logging.warning(f"Errore nella lettura del file email {email_file}: {e}")
        
        # Ordina le email per data (più recenti prima)
        emails.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return render_template('emails.html', emails=emails)
    except Exception as e:
        logging.error(f"Errore nel recupero delle email locali: {e}")
        flash(f'Errore nel recupero delle email: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/init_db')
def init_db():
    """Inizializza il database con dati di default."""
    
    # Controlla se esistono già dati
    if Category.query.count() > 0:
        flash('Il database è già stato inizializzato', 'info')
        return redirect(url_for('index'))
    
    try:
        # Dati di default per le categorie
        default_categories = [
            Category(name="Elettronica", description="Prodotti elettronici e tecnologici"),
            Category(name="Abbigliamento", description="Abbigliamento e accessori moda"),
            Category(name="Casa e Giardino", description="Prodotti per la casa e il giardino"),
            Category(name="Alimentari", description="Prodotti alimentari e bevande"),
            Category(name="Salute e Bellezza", description="Prodotti per la salute e la bellezza")
        ]
        
        db.session.add_all(default_categories)
        db.session.commit()
        
        # Template di esempio
        default_templates = [
            Template(
                name="Template Standard", 
                category_id=default_categories[0].id,
                content="Gentile [Nome Azienda],\n\nSiamo il team di C-Recenzione e vorremmo invitarvi a partecipare al nostro programma di recensioni.\n\nLe recensioni sono fondamentali per migliorare la visibilità dei vostri prodotti e aiutare i clienti a prendere decisioni informate.\n\nSaremmo felici di ricevere una vostra recensione completa e dettagliata.\n\nGrazie per la collaborazione,\n[Nome]"
            ),
            Template(
                name="Template Elettronica", 
                category_id=default_categories[0].id,
                content="Gentile [Nome Azienda],\n\nSiamo specialisti nel marketing di prodotti elettronici e stiamo cercando di ampliare la nostra base di recensioni per dispositivi innovativi.\n\nSaremmo interessati a ricevere un feedback dettagliato sui vostri prodotti, in particolare sulla qualità costruttiva, le funzionalità e l'esperienza utente.\n\nLe recensioni verranno pubblicate sulla nostra piattaforma specializzata nel settore tecnologico.\n\nCordiali saluti,\nTeam C-Recenzione"
            ),
            Template(
                name="Template Abbigliamento", 
                category_id=default_categories[1].id,
                content="Gentile [Nome Azienda],\n\nSiamo una piattaforma dedicata alle recensioni nel settore moda e abbigliamento.\n\nSaremmo interessati a ricevere un vostro feedback dettagliato sui vostri prodotti, concentrandovi su materiali, vestibilità e stile.\n\nLe vostre recensioni aiuteranno i consumatori a fare scelte consapevoli nel mondo della moda.\n\nDistinti saluti,\nTeam C-Recenzione"
            )
        ]
        
        db.session.add_all(default_templates)
        db.session.commit()
        
        # Impostazioni predefinite
        default_settings = {
            'kobold_api_url': 'http://localhost:5001/api',
            'use_fallback': True,
            'max_length': 1000,
            'temperature': 0.7
        }
        
        Setting.save_settings_dict(default_settings)
        
        flash('Database inizializzato con successo con dati di esempio', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Errore nell'inizializzazione del database: {str(e)}")
        flash(f'Errore nell\'inizializzazione del database: {str(e)}', 'danger')
    
    return redirect(url_for('index'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500