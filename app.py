import os
from flask import Flask, render_template, request
from data_models import Author, Book, db
from sqlalchemy import select

# 1. Flask-App instanziieren
app = Flask(__name__)

# 2. Absoluten Pfad berechnen (damit Flask die Datei auf dem Codio-Server garantiert findet)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'data/library.sqlite')}"

# 3. SQLAlchemy-Code mit der Flask-App verknüpfen
db.init_app(app)

# --- Route: Autoren Hinzufügen ---
@app.route('/add_author', methods=['GET', 'POST'])
def add_author():
    if request.method == 'POST':
        # Daten aus dem Formular abfangen
        name = request.form.get('name')
        birth_date = request.form.get('birthdate')
        date_of_death = request.form.get('date_of_death')

        # Neues Objekt Erstellen
        new_author = Author(name=name, birth_date=birth_date, date_of_death=date_of_death)

        # In die Datenbank schreiben
        db.session.add(new_author)
        db.session.commit()

        return render_template('add_author.html', success_message='Autor erfolgreich hinzugefügt!')
    
    return render_template('add_author.html')


# --- Route: Bücher Hinzufügen ---
@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        # Daten aus dem Formular abfangen
        isbn = request.form.get('isbn')
        title = request.form.get('title')
        publication_year = request.form.get('publication_year')
        author_id = request.form.get('author_id')
        
        # Neues Buch-Objekt erstellen
        new_book = Book(isbn=isbn, title=title, publication_year=publication_year, author_id=author_id)
        
        db.session.add(new_book)
        db.session.commit()

        # Autoren erneut laden, damit das Dropdown auch nach dem POST befüllt bleibt
        authors = db.session.scalars(select(Author)).all()
        return render_template('add_book.html', authors=authors, success_message="Buch erfolgreich hinzugefuegt!")
    
    # GET-Request: Alle Autoren laden, um sie im HTML-Dropdown anzuzeigen
    authors = db.session.scalars(select(Author)).all()
    return render_template('add_book.html', authors=authors)

# --- ROUTE: BUCH LÖSCHEN (UND EVENTUELL AUTOR OCH) ---
@app.route('/book/<int:book_id>/delete', methods=['POST'])
def delete_book(book_id):
    # 1. Das Buch aus der Datenbank holen
    book = db.session.get(Book, book_id)
    
    if book:
        author = book.author  # Den Autor merken, bevor das Buch gelöscht wird
        titel = book.title
        
        # 2. Buch löschen
        db.session.delete(book)
        db.session.commit()
        
        # 3. Prüfen, ob der Autor jetzt noch andere Bücher hat
        if author:
            # Wir schauen, ob noch Bücher mit dieser author_id existieren
            remaining_books = db.session.execute(
                select(Book).where(Book.author_id == author.id)
            ).scalars().all()
            
            # Wenn keine Bücher mehr übrig sind, löschen wir auch den Autor
            if not remaining_books:
                db.session.delete(author)
                db.session.commit()
                flash(f"'{titel}' wurde gelöscht. Da der Autor keine weiteren Bücher hatte, wurde er ebenfalls entfernt.")
                return redirect('/')
        
        flash(f"Das Buch '{titel}' wurde erfolgreich gespendet/gelöscht!")
    
    return redirect('/')


# --- ROUTE: STARTSEITE MIT SORTIERUNG & SUCHE ---
@app.route('/')
def home():
    # Parameter aus der URL abgreifen
    sort_by = request.args.get('sort_by', 'title')
    search_query = request.args.get('search', '').strip()
    
    # Basis-Abfrage erstellen
    stmt = select(Book)
    
    # Falls der User etwas ins Suchfeld eingegeben hat, filtern wir (wie SQL LIKE)
    if search_query:
        # %search_query% sucht überall im Titel nach dem Wort
        stmt = stmt.where(Book.title.ilike(f"%{search_query}%"))
    
    # Sortierung anwenden
    if sort_by == 'author':
        stmt = stmt.join(Author).order_by(Author.name.asc())
    else:
        stmt = stmt.order_by(Book.title.asc())
        
    books = db.session.scalars(stmt).all()
    
    return render_template('home.html', books=books)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)

# Temporär zum Erstellen der Tabellen eingefügt
#with app.app_context():
    #db.create_all()