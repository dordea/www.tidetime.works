from webapp import create_app # Importarea funcției create_app

app = create_app() # Crearea aplicației

if __name__ == '__main__': # Dacă fișierul este rulat direct
    app.run(debug=True, port=5000) # Pornim aplicația în modul de debug pe portul 5000
