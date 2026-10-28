# Brew & Bloom Coffee — Flask + SQLite backend

This folder turns the existing Brew & Bloom front end into a small full-stack college project.

## Features
- Preserves `index.html`, `style.css`, menu images and hero video paths.
- Python Flask backend.
- SQLite database (`brew_bloom.db`) created automatically on first run.
- Menu records are seeded into the database on first run.
- Menu Order buttons save orders to SQLite.
- Contact form saves messages to SQLite.
- Admin login, orders dashboard, order status updates, menu availability toggles.
- Admin can view contact messages.

## Folder structure
```text
brew_bloom_backend/
├── app.py
├── index.html
├── style.css
├── script.js
├── requirements.txt
├── README.md
├── brew_bloom.db       # created automatically; do not upload this if it has real customer data
├── images/             # copy your existing images here
├── videos/             # copy your existing coffee-video.mp4 here
└── templates/
    ├── admin.css
    ├── admin_login.html
    └── admin_dashboard.html
```

## Setup in VS Code (Windows PowerShell)

1. Extract the ZIP into a folder such as `C:\Users\YourName\Documents\brew_bloom_backend`.
2. Open that folder in VS Code: **File → Open Folder**.
3. Open **Terminal → New Terminal**.
4. Check Python is installed:
   ```powershell
   py --version
   ```
5. Create a virtual environment:
   ```powershell
   py -m venv .venv
   ```
6. Activate it in PowerShell:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, you can use the Command Prompt terminal and run:
   ```bat
   .venv\Scripts\activate.bat
   ```
7. Install Flask:
   ```powershell
   python -m pip install -r requirements.txt
   ```
8. Start the app:
   ```powershell
   python app.py
   ```
9. Open `http://127.0.0.1:5000` in your browser. **Do not double-click `index.html`**; use the Flask URL so the API can work.

## Admin login
- Open `http://127.0.0.1:5000/admin/login`
- Demo username: `admin`
- Demo password: `CoffeeDemo123!`

For a local college demo these defaults make setup easier. Before sharing the project, change the credentials in PowerShell before starting Flask:

```powershell
$env:BREW_ADMIN_USERNAME = "your_admin_name"
$env:BREW_ADMIN_PASSWORD = "your_strong_password"
$env:FLASK_SECRET_KEY = "replace-this-with-a-long-random-secret"
python app.py
```

Those variables apply to the current PowerShell terminal only. The app hashes the admin password before checking it. Do not deploy the Flask development server or demo credentials publicly.

## How it works
- `GET /api/menu` returns the available menu items as JSON.
- `POST /api/orders` validates and stores an order.
- `POST /api/contact` validates and stores a contact message.
- `/admin/login` checks admin credentials.
- `/admin` shows orders/messages and allows order status changes.
- `/admin/menu/<id>/availability` hides/shows an item for new orders.

SQLite data is saved in `brew_bloom.db` beside `app.py`.

## Media files
The supplied HTML references:
- `images/coffee-hero.png`
- `videos/coffee-video.mp4`

If those files are in your original project, copy your entire existing `images` and `videos` folders into this folder. Keep the same names and paths. The menu photos in the HTML currently use Unsplash URLs, so they require internet access.

## Test checklist
1. Start Flask and open the homepage using `http://127.0.0.1:5000`.
2. Click an **Order** button; enter name, email, quantity; confirm the order number appears.
3. Open `/admin/login` and sign in.
4. Confirm the order appears in the dashboard and change it to **Preparing**, then **Completed**.
5. Submit the contact form on the homepage and confirm the message appears in the dashboard.
6. Hide a menu item in the admin page and confirm its Order button reports that it is unavailable; make it available again.
7. Stop and restart Flask; confirm saved orders/messages remain.

## Important limitations and safety
- This is a local educational demo, not a production ordering/payment platform.
- It does not take payments, send emails, or provide delivery/pickup scheduling.
- For a public deployment, add CSRF protection, login rate limiting, secure environment configuration, HTTPS, production hosting, database backups, and a proper deployment server. Do not collect real customer data until the app has been reviewed and secured.
- Admin sessions use Flask's signed cookie session. Set a unique `FLASK_SECRET_KEY` before sharing or deploying.
- The database has no delete controls in this starter version, so test data remains until the database file is intentionally reset.
