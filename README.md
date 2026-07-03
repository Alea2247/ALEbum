# ALEbum - Flask + HTML

A simple photo album app with HTML frontend pages, a small JavaScript client, and a Flask backend that stores albums in SQLite.


## Files

- **app.py** - Flask app and SQLite API
- **index.html** - Main albums library page
- **create-album.html** - Create new album page
- **static/app.js** - Browser-side JavaScript that talks to Flask
- **static/styles.css** - All styling
- **static/img/** - Logo and images
- **albums.db** - SQLite database created on first run

## How to use

1. Install Python dependencies with `pip install -r requirements.txt`
2. Run `python app.py`
3. Open `http://127.0.0.1:5000/`
4. Create albums from the browser and they will be saved in SQLite

## Notes

The Flask backend exposes `GET /api/albums` and `POST /api/albums`.
The frontend pages use `fetch()` to load and create albums against that API.

If you want photo uploads or album detail pages next, those can be added as extra Flask routes and database tables.

## Customization

- Edit the HTML files to change page structure and copy
- Modify `static/app.js` to change API calls or page behavior
- Modify `static/styles.css` for styling changes
- Add your own logo to `static/img/logo.png`