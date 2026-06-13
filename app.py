import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from data_models import Author, Book, db
from sqlalchemy import select

# 1. Flask-App instanziieren
app = Flask(__name__)
app.secret_key = 'super_geheimes_schluessel_wort'  # Notwendig für die Flash-Nachrichten

# 2. Absoluten Pfad berechnen (damit Flask die Datei auf dem Codio-Server garantiert findet)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'data/library.sqlite')}"

# 3. SQLAlchemy-Code mit der Flask-App verknüpfen
db.init_app(app)


# Hilfsfunktion zur Validierung des Datumsformats
def validate_date(date_text):
    if not date_text:
        return True
    try:
        datetime.strptime(date_text, '%Y-%m-%d')
        return True
    except ValueError:
        return False


# --- Route: Autoren Hinzufügen ---
@app.route('/add_author', methods=['GET', 'POST'])
def add_author():
    if request.method == 'POST':
        # Daten aus dem Formular abfangen
        name = request.form.get('name', '').strip()
        birth_date = request.form.get('birthdate', '').strip()
        date_of_death = request.form.get('date_of_death', '').strip()

        # Validierung: Pflichtfelder prüfen
        if not name or not birth_date:
            flash("Name und Geburtsdatum sind erforderliche Felder.")
            return render_template('add_author.html')

        # Validierung: Datumsformate prüfen
        if not validate_date(birth_date) or (date_of_death and not validate_date(date_of_death)):
            flash("Ungültiges Datumsformat. Bitte nutzen Sie JJJJ-MM-TT.")
            return render_template('add_author.html')

        # Validierung: Logik der Lebensdaten prüfen
        if date_of_death and birth_date > date_of_death:
            flash("Das Sterbedatum kann nicht vor dem Geburtsdatum liegen.")
            return render_template('add_author.html')

        # Validierung: Duplikatsprüfung für Autoren
        existing_author = db.session.execute(
            select(Author).where(Author.name == name)
        ).scalars().first()

        if existing_author:
            flash("Dieser Autor existiert bereits in der Datenbank.")
            return render_template('add_author.html')

        # Neues Objekt Erstellen
        new_author = Author(name=name, birth_date=birth_date, date_of_death=date_of_death)

        # In die Datenbank schreiben mit Fehlerbehandlung
        try:
            db.session.add(new_author)
            db.session.commit()
            flash('Autor erfolgreich hinzugefügt!')
            return redirect(url_for('add_author'))
        except Exception:
            db.session.rollback()
            flash('Ein Datenbankfehler ist aufgetreten. Bitte versuchen Sie es erneut.')
            return render_template('add_author.html')

    return render_template('add_author.html')


# --- Route: Bücher Hinzufügen ---
@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    authors = db.session.scalars(select(Author)).all()

    if request.method == 'POST':
        # Daten aus dem Formular abfangen
        isbn = request.form.get('isbn', '').strip()
        title = request.form.get('title', '').strip()
        publication_year = request.form.get('publication_year', '').strip()
        author_id = request.form.get('author_id')

        # Validierung: Pflichtfelder prüfen
        if not isbn or not title or not author_id:
            flash("ISBN, Titel und Autor müssen angegeben werden.")
            return render_template('add_book.html', authors=authors)

        # Validierung: ISBN Format prüfen (nur Ziffern, Länge 10 oder 13)
        if not (isbn.isdigit() and len(isbn) in [10, 13]):
            flash("Die ISBN muss aus genau 10 oder 13 Ziffern bestehen.")
            return render_template('add_book.html', authors=authors)

        # Validierung: Erscheinungsjahr prüfen
        if not publication_year.isdigit() or int(publication_year) > datetime.now().year:
            flash("Bitte geben Sie ein gültiges Erscheinungsjahr an, das nicht in der Zukunft liegt.")
            return render_template('add_book.html', authors=authors)

        # Validierung: Doppelte ISBN in der Datenbank ausschließen
        existing_isbn = db.session.execute(
            select(Book).where(Book.isbn == isbn)
        ).scalars().first()

        if existing_isbn:
            flash("Ein Buch mit dieser ISBN existiert bereits.")
            return render_template('add_book.html', authors=authors)

        # Validierung: Doppelter Buchtitel für denselben Autor ausschließen
        existing_book = db.session.execute(
            select(Book).where(Book.title == title, Book.author_id == author_id)
        ).scalars().first()

        if existing_book:
            flash("Dieses Buch ist für den ausgewählten Autor bereits eingetragen.")
            return render_template('add_book.html', authors=authors)

        # Neues Buch-Objekt erstellen
        new_book = Book(isbn=isbn, title=title, publication_year=int(publication_year), author_id=author_id)

        # In die Datenbank schreiben mit Fehlerbehandlung
        try:
            db.session.add(new_book)
            db.session.commit()
            flash("Buch erfolgreich hinzugefuegt!")
            return redirect(url_for('add_book'))
        except Exception:
            db.session.rollback()
            flash("Fehler beim Speichern des Buches in der Datenbank.")
            return render_template('add_book.html', authors=authors)

    return render_template('add_book.html', authors=authors)


# --- ROUTE: BUCH LÖSCHEN (UND EVENTUELL AUTOR OCH) ---
@app.route('/book/<int:book_id>/delete', methods=['POST'])
def delete_book(book_id):
    # 1. Das Buch aus der Datenbank holen
    book = db.session.get(Book, book_id)

    if book:
        author = book.author  # Den Autor merken, bevor das Buch gelöscht wird
        titel = book.title

        try:
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
                    flash(
                        f"'{titel}' wurde gelöscht. Da der Autor keine weiteren Bücher hatte, wurde er ebenfalls entfernt.")
                    return redirect(url_for('home'))

            flash(f"Das Buch '{titel}' wurde erfolgreich gespendet/gelöscht!")
        except Exception:
            db.session.rollback()
            flash("Ein Fehler ist beim Löschvorgang aufgetreten.")

    return redirect(url_for('home'))


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