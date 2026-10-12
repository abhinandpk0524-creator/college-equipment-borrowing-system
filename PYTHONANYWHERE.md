# Complete Guide: Deploying to PythonAnywhere

This guide walks you step-by-step through hosting the **College Equipment Borrowing System** on [PythonAnywhere](https://www.pythonanywhere.com/).

---

## Prerequisites
- A **PythonAnywhere account** (free tier works great with SQLite).
- Your PythonAnywhere username (referred to as `<yourusername>` below, e.g., `abhinandpk`).

---

## Step 1: Open a Bash Console on PythonAnywhere

1. Log in to [PythonAnywhere](https://www.pythonanywhere.com/).
2. Go to the **Consoles** tab.
3. Click on **Bash** to open a new terminal session.

---

## Step 2: Clone Your Repository

In the Bash console, clone your project into a folder named `equipment_management`:

```bash
cd ~
git clone https://github.com/abhinandpk0524-creator/college-equipment-borrowing-system.git equipment_management
cd equipment_management
```

*(If your repo is already uploaded, navigate to the folder containing `manage.py`)*

---

## Step 3: Create a Python 3.10 Virtual Environment & Install Dependencies

In the same Bash console, run:

```bash
mkvirtualenv --python=/usr/bin/python3.10 equipment-management
pip install -r requirements.txt
```

> **Note:** Once activated, your console prompt will show `(equipment-management)`. Whenever you return later, activate it with:
> ```bash
> workon equipment-management
> ```

---

## Step 4: Run Migrations, Collect Static Files & Seed Demo Data

Run the following commands inside the `equipment_management` directory:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py seed_demo_data
```

*(Optional: If you want to create your own custom superuser account, also run `python manage.py createsuperuser`)*

`seed_demo_data` will automatically set up initial categories, equipment, and login accounts:
- **Admin:** `admin` / `admin123`
- **Staff:** `staff1` / `staff123`
- **Student:** `student1` / `student123`

---

## Step 5: Configure the Web App on PythonAnywhere

1. Click on the **Web** tab at the top of PythonAnywhere.
2. Click **Add a new web app**.
3. Choose **Manual configuration** (do **NOT** select the default Django wizard; manual configuration allows you to point to your existing code and virtual environment).
4. Select **Python 3.10**.
5. Finish the wizard.

---

## Step 6: Configure Paths and Virtual Environment in the Web Tab

Under the **Web** tab:

1. **Code section**:
   - **Source code:** `/home/<yourusername>/equipment_management`
   - **Working directory:** `/home/<yourusername>/equipment_management`
2. **Virtualenv section**:
   - Enter path: `/home/<yourusername>/.virtualenvs/equipment-management`
   *(Click the blue checkmark to save)*
3. **Static files section**:
   - Add a new entry:
     - **URL:** `/static/`
     - **Directory:** `/home/<yourusername>/equipment_management/staticfiles`

---

## Step 7: Configure the WSGI Configuration File

1. In the **Web** tab, click the link under **Code** labeled:
   `/var/www/<yourusername>_pythonanywhere_com_wsgi.py`
2. Delete everything inside the editor.
3. Paste the following configuration (replace `<yourusername>` with your actual PythonAnywhere username, e.g., `abhinandpk`):

```python
import os
import sys

# 1. Project path
project_home = '/home/<yourusername>/equipment_management'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# 2. Environment settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'equipment_project.settings'
os.environ['DJANGO_DEBUG'] = 'false'
os.environ['DJANGO_SECRET_KEY'] = 'production-secret-key-replace-with-any-random-string-123456789'
os.environ['DJANGO_ALLOWED_HOSTS'] = '<yourusername>.pythonanywhere.com,localhost,127.0.0.1'
os.environ['DJANGO_CSRF_TRUSTED_ORIGINS'] = 'https://<yourusername>.pythonanywhere.com'

# 3. Database: Defaults to SQLite. If you created a MySQL database on PythonAnywhere, uncomment below:
# os.environ['USE_MYSQL'] = 'true'
# os.environ['MYSQL_DATABASE'] = '<yourusername>$equipment_management'
# os.environ['MYSQL_USER'] = '<yourusername>'
# os.environ['MYSQL_PASSWORD'] = 'your_mysql_password'
# os.environ['MYSQL_HOST'] = '<yourusername>.mysql.pythonanywhere-services.com'

# 4. Start Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

4. Click **Save** (green button at top right).

---

## Step 8: Reload and Visit Your Site!

1. Go back to the **Web** tab.
2. Click the big green button **Reload <yourusername>.pythonanywhere.com**.
3. (Recommended) Scroll down to **Security** and toggle **Force HTTPS** to **ON**.
4. Visit your site at:
   `https://<yourusername>.pythonanywhere.com/`

You can test logging in right away with:
- `admin` / `admin123`
- `staff1` / `staff123`
- `student1` / `student123`

---

## (Optional) Daily Email & Due Date Reminder Task

To automate due date checks and sending email notifications:
1. Go to the **Tasks** tab on PythonAnywhere.
2. Under **Scheduled tasks**, set UTC time (e.g. `00:00`).
3. Set the command to:
   ```bash
   cd /home/<yourusername>/equipment_management && workon equipment-management && python manage.py send_borrow_reminders
   ```

---

## Troubleshooting & Common Questions

- **Page shows "Something went wrong" (Error 500)?**
  Go to the **Web** tab and check the **Error log** (`/var/log/<yourusername>.pythonanywhere.com.error.log`). The bottom few lines will show the exact Python traceback.
- **CSRF verification failed?**
  Ensure `https://<yourusername>.pythonanywhere.com` is in `DJANGO_CSRF_TRUSTED_ORIGINS` (already included in `settings.py`).
- **Styles / CSS missing in Django Admin?**
  Run `python manage.py collectstatic --noinput` in the Bash console and check that `/static/` is mapped to `/home/<yourusername>/equipment_management/staticfiles` in the Web tab.
- **Updating code in the future:**
  Whenever you push changes to GitHub, pull them in PythonAnywhere:
  ```bash
  cd ~/equipment_management
  git pull
  python manage.py migrate
  python manage.py collectstatic --noinput
  ```
  Then click **Reload** in the **Web** tab.
