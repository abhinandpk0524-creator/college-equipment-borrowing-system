# Deploying on PythonAnywhere

This project runs on Django 3.2 and uses PyMySQL for MySQL connections. Choose
Python 3.10 for the PythonAnywhere web app and virtual environment. Django 3.2
is end-of-life; upgrade Django before using the application for a public
production service.

## 1. Upload the project

Clone the project into your PythonAnywhere home directory or upload the source
files. The project root is the directory containing `manage.py`.

Do not upload the local `my_env` virtual environment. Install from
`requirements.txt` on PythonAnywhere instead.

## 2. Create the virtual environment

In a PythonAnywhere Bash console, replace `yourusername` with your account name:

```bash
cd /home/yourusername/equipment_management
mkvirtualenv --python=/usr/bin/python3.10 equipment-management
pip install -r requirements.txt
```

Use the same Python version for the web app and virtual environment.

## 3. Configure the database

In the PythonAnywhere **Databases** tab, create a MySQL database and note its
database name, username, host, and password. MySQL availability depends on the
PythonAnywhere account plan.

Set these environment variables for the site and for management commands:

```text
USE_MYSQL=true
MYSQL_DATABASE=yourusername$equipment_management
MYSQL_USER=yourusername
MYSQL_PASSWORD=your_mysql_password
MYSQL_HOST=the_host_shown_in_the_Databases_tab
```

Do not use the local Windows database settings or the SQLite development
database on the live site.

## 4. Set production environment variables

Set the following values in the PythonAnywhere WSGI configuration file before
`get_wsgi_application()` is called. Use your actual PythonAnywhere username.
Keep secrets out of Git and do not share them.

```python
import os

os.environ['DJANGO_DEBUG'] = 'false'
os.environ['DJANGO_SECRET_KEY'] = 'generate-a-long-random-secret'
os.environ['DJANGO_ALLOWED_HOSTS'] = 'yourusername.pythonanywhere.com'
os.environ['DJANGO_CSRF_TRUSTED_ORIGINS'] = 'https://yourusername.pythonanywhere.com'
os.environ['USE_MYSQL'] = 'true'
os.environ['MYSQL_DATABASE'] = 'yourusername$equipment_management'
os.environ['MYSQL_USER'] = 'yourusername'
os.environ['MYSQL_PASSWORD'] = 'your_mysql_password'
os.environ['MYSQL_HOST'] = 'the_host_shown_in_the_Databases_tab'

project_home = '/home/yourusername/equipment_management'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'equipment_project.settings')
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

Keep the PythonAnywhere-provided WSGI file's existing `sys` and `os` imports, or
add them before this snippet.

Generate a secret locally with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Use Django's production checks as a final review before launch.

## 5. Migrate and collect static files

Run these commands in a Bash console with the production environment variables
set in that console as well. Settings in the WSGI file do not automatically apply
to separate console commands.

```bash
cd /home/yourusername/equipment_management
workon equipment-management
export DJANGO_DEBUG=false
export DJANGO_SECRET_KEY='your-generated-secret'
export DJANGO_ALLOWED_HOSTS='yourusername.pythonanywhere.com'
export DJANGO_CSRF_TRUSTED_ORIGINS='https://yourusername.pythonanywhere.com'
export USE_MYSQL=true
export MYSQL_DATABASE='yourusername$equipment_management'
export MYSQL_USER='yourusername'
export MYSQL_PASSWORD='your_mysql_password'
export MYSQL_HOST='the_host_shown_in_the_Databases_tab'
python manage.py check --deploy
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

In the PythonAnywhere **Web** tab, map the URL `/static/` to
`/home/yourusername/equipment_management/staticfiles`.

## 6. Configure and reload the web app

In the **Web** tab, create a **Manual Configuration** web app using Python 3.10.
Set the virtualenv to `/home/yourusername/.virtualenvs/equipment-management`,
check the source code and working directory paths, update the PythonAnywhere
WSGI file as above, then click **Reload**.

Open `https://yourusername.pythonanywhere.com/`. For Django admin, visit
`https://yourusername.pythonanywhere.com/admin/`.

## Email and overdue reminders

The default email backend prints messages to the server log. Configure Django's
SMTP environment variables to send real approval and reminder emails. To create
the due-date and overdue in-app notifications and send their emails, add a
PythonAnywhere scheduled task that runs once each day:

```bash
cd /home/yourusername/equipment_management && workon equipment-management && python manage.py send_borrow_reminders
```

Set the same database variables for the scheduled task as for the web app.

For actual email delivery, configure `EMAIL_BACKEND` as
`django.core.mail.backends.smtp.EmailBackend` and set `EMAIL_HOST`, `EMAIL_PORT`,
`EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, and `EMAIL_USE_TLS` using your email
provider's SMTP credentials. The default console backend is for development.

## Existing local data

The production database starts separately from the Windows development database.
Migrations create its tables but do not copy existing users, equipment, or
requests. Export/import the records separately if you need to preserve them.
