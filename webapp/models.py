from . import db # Importarea instanței SQLAlchemy
from flask_login import UserMixin # Importarea clasei UserMixin
from sqlalchemy.sql import func # Importarea funcției func

class Note(db.Model): # Crearea unei clase pentru notițe
    id = db.Column(db.Integer, primary_key=True) # Crearea unui câmp pentru id-ul notiței
    date = db.Column(db.String(10000)) # Crearea unui câmp pentru data notiței
    project = db.Column(db.String(10000)) # Crearea unui câmp pentru proiectul notiței
    hours = db.Column(db.Integer) # Crearea unui câmp pentru orele notiței
    description = db.Column(db.String(10000)) # Crearea unui câmp pentru descrierea notiței
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) # Crearea unui câmp pentru id-ul utilizatorului

    __table_args__ = (db.UniqueConstraint('date', 'user_id', name='unique_date_user'),)


class User(UserMixin, db.Model): # Crearea unei clase pentru utilizatori
    id = db.Column(db.Integer, primary_key=True) # Crearea unui câmp pentru id-ul utilizatorului
    username = db.Column(db.String(15), unique=True) # Crearea unui câmp pentru numele de utilizator
    first_name = db.Column(db.String(30)) # Crearea unui câmp pentru prenumele utilizatorului
    last_name = db.Column(db.String(30)) # Crearea unui câmp pentru numele utilizatorului
    phone = db.Column(db.VARCHAR(9), unique=True) # Crearea unui câmp pentru numărul de telefon al utilizatorului
    company = db.Column(db.String(100)) # Crearea unui câmp pentru compania utilizatorului
    email = db.Column(db.String(50), unique=True) # Crearea unui câmp pentru email-ul utilizatorului
    password = db.Column(db.String(80)) # Crearea unui câmp pentru parola utilizatorului
    function = db.Column(db.String(100)) # Crearea unui câmp pentru funcția utilizatorului
    is_admin = db.Column(db.Boolean, default=False) # Crearea unui câmp pentru specificarea dacă utilizatorul este administrator
    dates = db.relationship('Note') # Crearea unei relații între utilizator și notițe

