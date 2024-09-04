from flask import Flask, redirect, flash, url_for, abort # Importarea claselor Flask
from flask_sqlalchemy import SQLAlchemy # Importarea clasei SQLAlchemy
from os import path # Importarea funcției path
import os
from flask_login import  login_required, current_user # Importarea funcțiilor login_required și current_user
from flask_login import LoginManager # Importarea clasei LoginManager
from flask_admin import Admin, AdminIndexView # Importarea claselor Admin și AdminIndexView
from flask_admin.contrib.sqla import ModelView # Importarea clasei ModelView
from flask_admin.menu import MenuLink # Importarea clasei MenuLink

db = SQLAlchemy() # Crearea unei instanțe SQLAlchemy
DB_NAME = "database.db" # Specificarea numelui bazei de date
# Obține directorul curent al scriptului
current_dir = os.path.dirname(__file__)

# Funcție pentru a căuta fișierul în toate directoarele începând de la un director specificat
def search_for_file(file_name, start_dir):
    for dirpath, _, filenames in os.walk(start_dir):
        if file_name in filenames:
            return os.path.join(dirpath, file_name)
    return None

# Caută fișierul database.db în toate directoarele începând de la directorul curent al scriptului
db_file_path = search_for_file("database.db", current_dir)

def create_app(): # Crearea unei funcții pentru crearea aplicației
    app = Flask(__name__) # Crearea unei instanțe Flask
    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjss' # Specificarea unei chei secrete pentru sesiune
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_file_path}' # Specificarea bazei de date
    db.init_app(app) # Inițializarea bazei de date


    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/') # Înregistrarea blueprint-ului pentru vizualizări
    app.register_blueprint(auth, url_prefix='/') # Înregistrarea blueprint-ului pentru autentificare

    from .models import User, Note

    class AdminAuthenticationView(AdminIndexView): # Crearea unei clase pentru autentificarea administratorului
        def is_accessible(self):  # Crearea unei funcții pentru verificarea autentificării administratorului
            if current_user.is_admin == True: # Dacă utilizatorul este administrator
                return current_user.is_authenticated # Returnăm dacă utilizatorul este autentificat
            else: # Dacă utilizatorul nu este administrator
                return abort(404) # Returnăm eroare 404

        def inaccessible_callback(self, name, **kwargs): # Crearea unei funcții pentru redirecționarea utilizatorilor neautentificați
            flash('You must be logged in to access this page', 'error') # Afisăm un mesaj de eroare
            return redirect(url_for('auth.login')) # Redirecționăm utilizatorul către pagina de autentificare


    admin = Admin(app, name='Admin Panel', template_mode='bootstrap3', index_view=AdminAuthenticationView()) # Crearea unei instanțe Admin
    admin.add_view(ModelView(User, db.session)) # Adăugarea unei vizualizări pentru utilizatori
    #admin.add_view(ModelView(Note, db.session)) # Adăugarea unei vizualizări pentru notițe
    admin.add_link(MenuLink(name='Home', url='/')) # Adăugarea unui link către pagina principală

    with app.app_context(): # Crearea unei instanțe Flask
        #db.drop_all() # Ștergerea bazei de date
        db.create_all() # Crearea bazei de date

    login_manager = LoginManager() # Crearea unei instanțe LoginManager
    login_manager.login_view = 'auth.login' # Specificarea rutei pentru autentificare
    login_manager.init_app(app) # Inițializarea LoginManager


    @login_manager.user_loader # Decorator pentru încărcarea utilizatorului
    def load_user(id): # Crearea unei funcții pentru încărcarea utilizatorului
        return User.query.get(int(id)) # Returnăm utilizatorul cu id-ul specificat

    return app # Returnăm aplicația


def create_database(app): # Crearea unei funcții pentru crearea bazei de date
    if not path.exists('website/' + DB_NAME): # Dacă baza de date nu există
        db.create_all(app=app) # Crearea bazei de date
        print('Created Database!') # Afisăm un mesaj de succes