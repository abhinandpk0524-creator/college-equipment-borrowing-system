# College Equipment Borrowing and Inventory Management System

A Django web app for managing equipment inventory, categories, borrowing
requests, returns, damage reports, and due-date notifications. It supports
student, staff, and administrator roles.

## Requirements

- Python 3.10 or later
- Dependencies from `requirements.txt`

## Run locally

From the directory containing `manage.py`:

```bash
python -m venv .venv
```

Activate the virtual environment, then run:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`; the Django admin is at
`http://127.0.0.1:8000/admin/`.

The local settings use SQLite by default. For MySQL, set `USE_MYSQL=true` and
provide `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`, and `MYSQL_HOST` as
environment variables.

## Notifications

Approval and due-date emails use Django's configured email backend. For
development, the default console backend prints email contents in the terminal.
Configure SMTP environment variables to send real email. Run
`python manage.py send_borrow_reminders` daily to create due-date/overdue
notifications and send pending emails.

## PythonAnywhere

See [PYTHONANYWHERE.md](PYTHONANYWHERE.md) for deployment instructions.

## Checks and tests

```bash
python manage.py check
python manage.py test equipment
```
