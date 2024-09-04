from flask import Blueprint, render_template, request, flash, redirect, url_for # Importarea funcțiilor și claselor necesare
from .models import User # Importarea clasei User
from werkzeug.security import generate_password_hash, check_password_hash  # Importarea funcțiilor pentru criptarea parolei
from . import db # Importarea instanței SQLAlchemy
import re # Importarea modulului re
from flask_login import login_user, login_required, logout_user, current_user # Importarea funcțiilor și claselor necesare


auth = Blueprint('auth', __name__) # Cream unui obiect Blueprint pentru autentificare

@auth.route('/login', methods=['GET', 'POST']) # Cream unei rute pentru autentificare
def login(): # Crearea unei funcții pentru autentificare
    if request.method == 'POST': # Dacă metoda cererii este POST
        email = request.form.get('email') # Obținem valoarea introdusă în câmpul email
        password = request.form.get('password') # Obținem valoarea introdusă în câmpul parolă

        user = User.query.filter_by(email=email).first() # Obținem primul utilizator cu email-ul introdus

        if user: # Dacă utilizatorul există
            if user.password==password: # Dacă parola introdusă este aceeași cu parola utilizatorului
                flash('Logged in successfully!', category='success') # Afisăm un mesaj de succes
                login_user(user, remember=True) # Autentificăm utilizatorul
                return redirect(url_for('views.home')) # Redirecționăm utilizatorul către pagina principală
            else: # Dacă parola introdusă nu este aceeași cu parola utilizatorului
                flash('Incorrect password, try again.', category='error') # Afisăm un mesaj de eroare
        else: # Dacă utilizatorul nu există
            flash('Email does not exist.', category='error') # Afisăm un mesaj de eroare
    return render_template("login.html", user=current_user) # Returnăm șablonul pentru autentificare

@auth.route('/logout') # Cream o rută pentru deautentificare
@login_required # Specificăm că utilizatorul trebuie să fie autentificat pentru a accesa această rută
def logout(): # Crearea unei funcții pentru deautentificare
    logout_user() # Deautentificăm utilizatorul
    return redirect(url_for('auth.login')) # Redirecționăm utilizatorul către pagina de autentificare


@auth.route('/home') # Cream o rută pentru pagina principală
@login_required # Specificăm că utilizatorul trebuie să fie autentificat pentru a accesa această rută
def home(): # Crearea unei funcții pentru pagina principală
    return render_template("home.html", user=current_user) # Returnăm șablonul pentru pagina principală

@auth.route('/contacts') # Cream o rută pentru pagina de contacte
@login_required # Specificăm că utilizatorul trebuie să fie autentificat pentru a accesa această rută
def contacts(): # Cream unei funcții pentru pagina de contacte
    return render_template("contacts.html", user=current_user) # Returnăm șablonul pentru pagina de contacte

@auth.route('/about') # Cream o rută pentru pagina de contacte
def about(): # Cream unei funcții pentru pagina de contacte
    return render_template("about.html", user=current_user) # Returnăm șablonul pentru pagina de contacte

@auth.route('/sign-up', methods=['GET', 'POST']) # Cream o rută pentru înregistrare
def sign_up(): # Crearea unei funcții pentru înregistrare
    if request.method == 'POST': # Dacă metoda cererii este POST
        email = request.form.get('email') # Obținem valoarea introdusă în câmpul email
        first_name = request.form.get('firstName') # Obținem valoarea introdusă în câmpul prenume
        last_name = request.form.get('lastName') # Obținem valoarea introdusă în câmpul nume
        phone = request.form.get('phone') # Obținem valoarea introdusă în câmpul telefon
        company = request.form.get('company').upper() # Obținem valoarea introdusă în câmpul companie
        function = request.form.get('function').lower() # Obținem valoarea introdusă în câmpul funcție
        username = request.form.get('username') # Obținem valoarea introdusă în câmpul utilizator
        password = request.form.get('password') # Obținem valoarea introdusă în câmpul parolă
        password2 = request.form.get('confirm_password') # Obținem valoarea introdusă în câmpul confirmare parolă
        user = User.query.filter_by(email=email).first() # Obținem primul utilizator cu email-ul introdus
        user2 = User.query.filter_by(username=username).first() # Obținem primul utilizator cu utilizatorul introdus
        if function == "administrator": # Dacă funcția este administrator
            is_admin = True # Specificăm că utilizatorul este administrator
        else: # Dacă funcția nu este administrator
            is_admin = False # Specificăm că utilizatorul nu este administrator
        if user or user2: # Dacă utilizatorul sau utilizatorul2 există
            if user2:flash('Username already exists.', category='error') # Afisăm un mesaj de eroare dacă utilizatorul2 există
            elif user:flash('Email already exists.', category='error') # Afisăm un mesaj de eroare dacă utilizatorul există
        elif len(email) < 4: # Dacă email-ul are mai puțin de 4 caractere
            flash('Email must be greater than 4 characters.', category='error') # Afisăm un mesaj de eroare
        elif len(first_name) < 2: # Dacă prenumele are mai puțin de 2 caractere
            flash('First name must be greater than 2 characters.', category='error') # Afisăm un mesaj de eroare
        elif len(last_name) < 2: # Dacă numele are mai puțin de 2 caractere
            flash('Last name must be greater than 2 characters.', category='error') # Afisăm un mesaj de eroare
        elif not re.match(r'^[0-9]{9}$', phone):  # Validarea numărului de telefon cu expresia regulată
            flash('Phone number must be exactly 9 digits.(Without country code)', category='error') # Afisăm un mesaj de eroare
        elif len(username) < 2: # Dacă utilizatorul are mai puțin de 2 caractere
            flash('Username must be greater than 2 characters.', category='error') # Afisăm un mesaj de eroare
        elif password != password2: # Dacă parola nu este aceeași cu confirmarea parolei
            flash('Passwords don\'t match.', category='error') # Afisăm un mesaj de eroare
        elif len(password) < 7: # Dacă parola are mai puțin de 7 caractere
            flash('Password must be at least 7 characters.', category='error') # Afisăm un mesaj de eroare
        else: # Dacă toate condițiile sunt îndeplinite
            new_user = User(email=email, first_name=first_name, last_name=last_name,phone=phone, company=company, is_admin=is_admin,function=function, username=username, password=password) # Creăm un utilizator nou cu datele introduse
            db.session.add(new_user) # Adăugăm utilizatorul nou în baza de date
            db.session.commit() # Salvăm modificările
            login_user(new_user, remember=True) # Autentificăm utilizatorul nou
            flash('Account created!', category='success') # Afisăm un mesaj de succes
            return redirect(url_for('views.home')) # Redirecționăm utilizatorul către pagina principală
    return render_template("sign_up.html", user=current_user) # Returnăm șablonul pentru înregistrare
