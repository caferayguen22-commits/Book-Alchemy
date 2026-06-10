from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Author(db.Model):
    __tablename__ = 'authors'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    birth_date = db.Column(db.String)
    date_of_death = db.Column(db.String)

    def __str__(self):
        return f"Author {self.name}"
    
    def __repr__(self):
        return f"<Author {self.id}>"


class Book(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    isbn = db.Column(db.String)
    title = db.Column(db.String, nullable=False)
    publication_year = db.Column(db.Integer)

    # Fremdschlüssel zur Tabelle authors
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'))

    # Verbindung zum Author-Modell herstellen
    author = db.relationship('Author', backref='books')

    def __str__(self):
        return f" Book {self.title}"
    
    def __repr__(self):
        return f"<Book {self.id}>"