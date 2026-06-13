# Book Alchemy 🧪📚

A stylish Flask web application designed to manage a local library of books and authors, styled with the Bulma CSS framework.

## Features
- **Author Management:** Add authors with birth and death dates, preventing duplicates.
- **Book Management:** Log books with unique ISBN numbers and publication years.
- **Automated Cleanup:** When the last book of an author is deleted, the author is automatically removed from the database.
- **Search & Sort:** Easily filter books by title and sort them alphabetically by title or author name.

## Technologies Used
- Python 3
- Flask
- Flask-SQLAlchemy (SQLite)
- Bulma CSS