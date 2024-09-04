from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, send_file # Importarea funcțiilor și claselor necesare din Flask
from flask_login import  login_required, current_user # Importarea funcțiilor și claselor necesare pentru autentificare
from .models import Note, User, db # Importarea claselor și a instanței bazei de date
from datetime import date, datetime # Importarea claselor pentru lucrul cu datele și timpul
from apscheduler.schedulers.background import BackgroundScheduler # Importarea clasei pentru programarea sarcinilor periodice
from collections import defaultdict # Importarea clasei pentru crearea unui dicționar cu valori implicite
from sqlalchemy import extract # Importarea funcției pentru extragerea datelor din baza de date
import pandas as pd # Importarea bibliotecii pentru lucrul cu datele în format tabular
import openpyxl # Importarea bibliotecii pentru lucrul cu fișierele Excel
from io import BytesIO # Importarea clasei pentru lucrul cu fluxurile de octeți
import calendar # Importarea clasei pentru lucrul cu calendarul
import sqlalchemy # Importarea clasei pentru lucrul cu baza de date
import csv # Importarea clasei pentru lucrul cu fișierele CSV
import tempfile # Importarea clasei pentru lucrul cu fișierele temporare

# Inițializarea unui Blueprint Flask pentru aceste rute
views = Blueprint('views', __name__)

# Dicționarul pentru a stoca totalul de ore pentru fiecare utilizator în fiecare lună
monthly_totals = {}

# Crearea unui scheduler pentru a programa acțiuni periodice
scheduler = BackgroundScheduler()


def check_database(): # Funcția care verifică baza de date și returnează înregistrările pentru fiecare lună
    # Inițializează un dicționar pentru a stoca numele lunilor cu înregistrări ale utilizatorului curent
    months_with_records = defaultdict(list) # Un dicționar pentru a stoca înregistrările pentru fiecare lună
    months_with_totals = {} # Un dicționar pentru a stoca totalul de ore pentru fiecare lună

    # Obține toate înregistrările din baza de date pentru utilizatorul curent
    all_notes = Note.query.filter_by(user_id=current_user.id).all()

    # Parcurge fiecare înregistrare și adaugă înregistrările corespunzătoare lunii în dicționar
    for note in all_notes: # Parcurgem fiecare înregistrare a utilizatorului curent
        note_date = datetime.strptime(note.date, '%Y-%m-%d') # Obținem data înregistrării
        month_name = note_date.strftime("%B") # Obținem numele lunii
        months_with_records[month_name].append({ # Adăugăm înregistrarea în dicționarul corespunzător lunii
            'date': note.date, # Data înregistrării
            'hours': note.hours, # Numărul de ore
            'project': note.project, # Proiectul
            'description': note.description # Descrierea
        }) # Adăugăm înregistrarea în dicționarul corespunzător lunii

    # Calculează totalul orelor pe fiecare lună și adaugă totalul în dicționarul separat
    for month, records in months_with_records.items(): # Parcurgem fiecare lună și înregistrările corespunzătoare
        total_hours = sum(record['hours'] for record in records) # Calculăm totalul de ore pentru fiecare lună
        months_with_totals[month] = { # Adăugăm totalul de ore pentru fiecare lună în dicționarul separat
            'records': records, # Înregistrările pentru lună
            'total_hours': total_hours # Totalul de ore pentru lună
        } # Adăugăm totalul de ore pentru fiecare lună în dicționarul separat

    return months_with_totals # Returnăm dicționarul cu totalul de ore pentru fiecare lună


def scheduled_task(): # Funcția pentru programarea sarcinilor periodice
    # Calcularea totalului de ore pentru fiecare utilizator și stocarea acestuia în dicționar
    details = [] # O listă pentru a stoca detaliile pentru toți utilizatorii
    users_same_company = User.query.filter_by(company=current_user.company).all() # Obținem toți utilizatorii din aceeași companie
    for user in users_same_company: # Parcurgem fiecare utilizator și calculam totalul de ore pentru fiecare utilizator
        user_total = totals(user.id) # Obținem totalul de ore pentru utilizatorul curent
        user_details = [] # O listă pentru a stoca detaliile pentru utilizatorul curent
        current_date = datetime.now() # Obținem data curentă
        first_day_of_month = datetime(current_date.year, current_date.month, 1) # Obținem prima zi a lunii curente

        for note in user.dates: # Parcurgem fiecare înregistrare a utilizatorului și adăugăm detaliile pentru utilizatorul curent
            note_date = datetime.strptime(note.date, '%Y-%m-%d') # Obținem data înregistrării
            if note_date >= first_day_of_month and note_date <= current_date: # Verificăm dacă înregistrarea este în luna curentă
                user_details.append({ # Adăugăm detaliile în lista de detalii pentru utilizatorul curent
                    'date': note.date, # Data înregistrării
                    'hours': note.hours,  # Numărul de ore
                    'project': note.project, # Proiectul
                    'description': note.description # Descrierea
                })
        details.extend(user_details) # Adăugăm detaliile pentru utilizatorul curent la lista globală de detalii
        monthly_totals[user.id] = { # Adăugăm totalul de ore pentru utilizatorul curent în dicționarul global
            'total': user_total, # Totalul de ore pentru utilizator
            'month': datetime.now().strftime("%B"), # Numele lunii curente
            'details': user_details # Detaliile pentru utilizatorul curent
        }
    monthly_totals['details'] = details # Adăugăm detalii pentru toți utilizatorii în dicționarul global
scheduler.add_job(scheduled_task, 'cron', hour=0) # Adăugarea sarcinii periodice la scheduler
scheduler.start() # Pornirea schedulerului


@views.route("/download_data", methods=["GET"]) # Ruta pentru descărcarea datelor
@login_required # Asigurarea că utilizatorul este autentificat
def download_data(): # Funcția pentru descărcarea datelor
    """
    Funcția pentru descărcarea datelor în format Excel pentru luna curentă, sortate pe lună și an, cu denumirea lunii în antet.
    """
    current_month = datetime.now().month # Obține luna curentă
    current_year = datetime.now().year # Obține anul curent
    all_users = User.query.filter_by(company=current_user.company).all() # Obține toți utilizatorii din aceeași companie
    wb = openpyxl.Workbook() # Creează un workbook Excel
    ws = wb.active # Creează o foaie de lucru
    month_name = calendar.month_name[current_month] # Obține numele lunii curente
    ws.append(['Nume', 'Prenume', 'Data', 'Ore', 'Proiect', 'Descriere', 'Luna']) # Adaugă antetele în fișierul Excel
    sorted_notes = [] # O listă pentru a stoca toate notele sortate
    # Adaugă datele pentru fiecare utilizator pentru luna curentă
    for user in all_users: # Parcurgem fiecare utilizator
        for note in user.dates: # Parcurgem fiecare înregistrare a utilizatorului
            note_date = datetime.strptime(note.date, '%Y-%m-%d') # Obținem data înregistrării
            if note_date.month == current_month and note_date.year == current_year: # Verificăm dacă înregistrarea este în luna curentă
                sorted_notes.append((note_date, user.last_name, user.first_name, note.date, note.hours, note.project, note.description)) # Adăugăm înregistrarea în lista de note sortate
    sorted_notes.sort(key=lambda x: x[1]) # Sortează notele după numele de familie al utilizatorului
    # Adaugă datele sortate în fișierul Excel
    for note_data in sorted_notes: # Parcurgem fiecare înregistrare sortată
        ws.append([note_data[1], note_data[2], note_data[3], note_data[4], note_data[5], note_data[6], month_name]) # Adaugăm înregistrarea în fișierul Excel
    # Salvează workbook-ul într-un flux BytesIO
    excel_file = BytesIO() # Creează un flux BytesIO
    file_name = f'database_{current_user.company.lower()}_{calendar.month_name[current_month]}.xlsx'  # Creează un nume de fișier
    wb.save(excel_file) # Salvează workbook-ul în fluxul BytesIO
    excel_file.seek(0) # Setează cursorul la începutul fișierului
    return send_file(excel_file, as_attachment=True, download_name=file_name) # Returnează fișierul pentru descărcare

@views.route("/download_data_csv", methods=["GET"]) # Ruta pentru descărcarea datelor în format CSV
@login_required # Asigurarea că utilizatorul este autentificat
def download_data_csv(): # Funcția pentru descărcarea datelor în format CSV
    """
    Funcția pentru descărcarea datelor în format CSV pentru luna curentă, sortate pe lună și an, cu denumirea lunii în antet.
    """
    current_month = datetime.now().month # Obține luna curentă
    current_year = datetime.now().year # Obține anul curent
    all_users = User.query.filter_by(company=current_user.company).all() # Obține toți utilizatorii din aceeași companie
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file: # Creează un fișier temporar CSV
        csv_writer = csv.writer(tmp_file) # Creează un obiect CSV writer
        csv_writer.writerow(['Nume', 'Prenume', 'Data', 'Ore', 'Proiect', 'Descriere', 'Luna']) # Adaugă antetele în fișierul CSV
        # Adaugă datele pentru fiecare utilizator pentru luna curentă
        for user in all_users: # Parcurgem fiecare utilizator
            for note in user.dates: # Parcurgem fiecare înregistrare a utilizatorului
                note_date = datetime.strptime(note.date, '%Y-%m-%d') # Obținem data înregistrării
                if note_date.month == current_month and note_date.year == current_year: # Verificăm dacă înregistrarea este în luna curentă
                    csv_writer.writerow([user.last_name, user.first_name, note.date, note.hours, note.project, note.description, calendar.month_name[current_month]]) # Adaugăm înregistrarea în fișierul CSV
    return send_file(tmp_file.name, as_attachment=True, download_name=f'database_{current_user.company.lower()}_{calendar.month_name[current_month]}.csv', mimetype='text/csv') # Returnează fișierul pentru descărcare




@views.route('/control_panel', methods=['GET', 'POST']) # Ruta pentru panoul de control
@login_required # Asigurarea că utilizatorul este autentificat
def control_panel(): # Funcția pentru panoul de control
    scheduled_task() # Apelarea funcției pentru programarea sarcinilor periodice
    if current_user.is_admin: # Verificăm dacă utilizatorul curent este un administrator
        users_same_company = User.query.filter_by(company=current_user.company).all() # Obținem toți utilizatorii din aceeași companie
        counted_details = {}  # Un dicționar pentru a stoca numărul de înregistrări pentru fiecare utilizator
        details = {} # Un dicționar pentru a stoca detaliile pentru fiecare utilizator
        first_day_of_month = datetime(datetime.now().year, datetime.now().month, 1) # Obținem prima zi a lunii curente
        current_date = datetime.now() # Obținem data curentă
        for user in users_same_company: # Parcurgem fiecare utilizator și numărăm înregistrările pentru fiecare utilizator
            details[user.id] = Note.query.filter_by(user_id=user.id).filter(extract('year', Note.date) == current_date.year, extract('month', Note.date) == current_date.month).all() # Obținem toate înregistrările pentru utilizatorul curent în luna curentă
            counted_details[user.id] = Note.query.filter_by(user_id=user.id).filter(extract('year', Note.date) == current_date.year, extract('month', Note.date) == current_date.month).count() # Numărăm înregistrările pentru utilizatorul curent în luna curentă
        return render_template('control_panel.html', users=users_same_company, user=current_user,  monthly_totals=monthly_totals,details=details,counted=counted_details) # Returnăm șablonul pentru panoul de control
    else: # Dacă utilizatorul curent nu este un administrator
        flash('You are not authorized to access this page.', 'error') # Afisăm un mesaj de eroare dacă utilizatorul nu este autorizat
        return redirect(url_for('views.home')) # Redirecționăm utilizatorul la pagina principală


@views.route("/update_data", methods=["POST"]) # Ruta pentru actualizarea datelor
def update_data(): # Funcția pentru actualizarea datelor
    data = request.json # Obținem datele trimise de la clientul de la răspunsul la cerere
    #cautam inregistrarea doar pentru id curent
    note = Note.query.filter_by(date=data['date'], user_id=current_user.id).first() # Căutăm înregistrarea cu data specificată și id-ul utilizatorului curent în baza de date
    if note: # Verificăm dacă s-a gasit înregistrarea
        note.project = data['project'] # Actualizăm datele înregistrării
        note.hours = data['hours'] # Actualizăm datele înregistrării
        note.description = data['description']  # Actualizăm datele înregistrării
        db.session.commit() # Salvăm modificările în baza de date
        flash(f'S-au actualizat datele pentru ziua {data["date"]}', category='success') # Afisăm un mesaj de succes
        return jsonify({'message': 'Record updated successfully'}) # Returnăm un mesaj de succes
    else: # Dacă nu s-a gasit înregistrarea
        flash(f'Nu s-au gasit date pentru ziua {data["date"]}', category='error') # Afisăm un mesaj de eroare
        return jsonify({'error': 'No record found for the provided date'}) # Returnăm un mesaj de eroare


@views.route("/contacts") # Ruta pentru pagina de contacte
@login_required # Asigurarea că utilizatorul este autentificat
def contacts(): # Funcția pentru pagina de contacte
    users_same_company = User.query.filter_by(company=current_user.company).all() # Obținem toți utilizatorii din aceeași companie
    return render_template("contacts.html", user=current_user,users_same_company=users_same_company) # Returnăm șablonul pentru pagina de contacte


def get_curent_date(): # Funcția pentru a obține data curentă
    today = date.today() # Obținem data curentă
    return today.strftime("%m/%d/%Y") # Returnăm data curentă în formatul specificat


@login_required # Asigurarea că utilizatorul este autentificat
def totals(user_id=None): # Funcția pentru a calcula totalul de ore pentru utilizatorul curent
    total = 0 # Inițializăm totalul de ore cu 0
    current_date = datetime.now() # Obținem data curentă
    current_month = current_date.month # Obținem luna curentă
    current_year = current_date.year # Obținem anul curent

    if user_id: # Verificăm dacă s-a furnizat un ID de utilizator
        user = User.query.get(user_id) # Obținem utilizatorul cu ID-ul specificat
        for note in user.dates: # Parcurgem fiecare înregistrare a utilizatorului și adăugăm orele pentru luna curentă
            note_date = datetime.strptime(note.date, '%Y-%m-%d') # Obținem data înregistrării
            if note_date.month == current_month and note_date.year == current_year: # Verificăm dacă înregistrarea este în luna curentă
                total += note.hours # Adăugăm orele înregistrării la total
    else: # Dacă nu s-a furnizat un ID de utilizator
        for note in current_user.dates: # Parcurgem fiecare înregistrare a utilizatorului curent și adăugăm orele pentru luna curentă
            note_date = datetime.strptime(note.date, '%Y-%m-%d') # Obținem data înregistrării
            if note_date.month == current_month and note_date.year == current_year: # Verificăm dacă înregistrarea este în luna curentă
                total += note.hours # Adăugăm orele înregistrării la total
    return total # Returnăm totalul de ore pentru utilizatorul curent


@views.route('/monthly_statement', methods=['GET', 'POST']) # Ruta pentru declarația lunară
@login_required # Asigurarea că utilizatorul este autentificat
def monthly_statement(): # Funcția pentru declarația lunară
    current_month = datetime.now().strftime("%B") # Obținem numele lunii curente
    return render_template('monthly_statement.html', user=current_user,current_month=current_month, months_with_totals=check_database()) # Returnăm șablonul pentru declarația lunară

from sqlalchemy.exc import IntegrityError
@views.route('/', methods=['GET', 'POST']) # Ruta pentru pagina principală
@login_required # Asigurarea că utilizatorul este autentificat
def home(): # Funcția pentru pagina principală
    scheduled_task() # Apelarea funcției pentru programarea sarcinilor periodice
    if request.method == 'POST': # Verificăm dacă s-a trimis o cerere de tip POST
        date = request.form.get('date') # Obținem data trimisă de la client
        project = request.form.get('project') # Obținem proiectul trimis de la client
        hours = request.form.get('hours') # Obținem numărul de ore trimis de la client
        description = request.form.get('description') # Obținem descrierea trimisă de la client
        #verificam daca exista deja o inregistrare pe data curenta de la utilizatorul cu idul curent
        print(date)
        # cautam inregistrarea doar pentru id curent
        note = Note.query.filter_by(date=date,user_id=current_user.id).first()  # Căutăm înregistrarea cu data specificată și id-ul utilizatorului curent în baza de date
        if note:  # Verificăm dacă s-a gasit înregistrarea
            note.project = project  # Actualizăm datele înregistrării
            note.hours = hours  # Actualizăm datele înregistrării
            note.description = description  # Actualizăm datele înregistrării
            db.session.commit()  # Salvăm modificările în baza de date
            flash(f'S-au actualizat datele pentru ziua {date}', category='success')  # Afisăm un mesaj de succes
            return redirect(url_for('views.home'))  # Redirecționăm utilizatorul la pagina principală
        # Verificăm dacă există deja o înregistrare pentru această dată
            exist = Note.query.filter_by(date=date, user_id=current_user.id).first()
            if exist:
                flash('The entry for this date already exists!', category='error')
                return redirect(url_for('views.home'))
            elif not hours.isdigit() or int(hours) < 1:  # Verificăm dacă numărul de ore este valid
                flash('Please enter a valid number of hours!', category='error')
        else:
            try:
                # Dacă nu există deja o înregistrare pentru această dată și numărul de ore este mai mare sau egal cu 1
                new_dates = Note(date=date, project=project, hours=hours, description=description, user_id=current_user.id) # Creăm o nouă înregistrare
                db.session.add(new_dates) # Adăugăm înregistrarea în sesiunea bazei de date
                db.session.commit() # Salvăm înregistrarea în baza de date
                flash(f'S-au inregistrat {date} aceasta data', category='success') # Afisăm un mesaj de succes
            except IntegrityError:
                db.session.rollback()
                flash('The entry for this date already exists!', category='error')
            except sqlalchemy.exc.DataError:
                db.session.rollback()
                flash('The entry for this date already exists!', category='error')
            except Exception as e:
                db.session.rollback()
                flash('An error occurred while adding the entry. Please try again later.', category='error')

            return redirect(url_for('views.home')) # Redirecționăm utilizatorul la pagina principală

    return render_template("home.html", user=current_user,date=get_curent_date(), total=totals(current_user.id), monthly_totals=monthly_totals) # Returnăm șablonul pentru pagina principală


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
@views.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form['email']
        message = request.form['message']
        # Configurarea serverului SMTP
        smtp_server = 'smtp.mail.ru'
        smtp_port = 587
        smtp_username = 'feedback.user@list.ru'
        smtp_password = 'ckaVZd32UnqiGzX32SY3'
        try:
            # Crearea mesajului email
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = 'feedback.user@list.ru'
            msg['Subject'] = f'Feedback de la {name}'
            body = f"Nume: {name}\nEmail: {email}\nMesaj: {message}"
            msg.attach(MIMEText(body, 'plain'))
            # Trimiterea email-ului
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            server.quit()
            flash('Feedback-ul tău a fost trimis cu succes!', 'success')
        except Exception as e:
            flash('A apărut o problemă la trimiterea feedback-ului. Încearcă din nou mai târziu.', 'danger')
        return redirect('/feedback')
    return render_template('feedback.html',user=current_user)