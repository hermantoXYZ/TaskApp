
## 📦 Instalasi & Setup Lokal (Development)

### 1. Clone repository

```bash
git clone https://github.com/hermantoXYZ/TaskApp.git
cd TaskApp
```

---

### 2. Pastikan Python dan pip tersedia

Cek versi:

```bash
python --version
pip --version
```

---

### 3. Buat virtual environment

```bash
python -m venv env
```

Aktifkan environment:

**Windows:**

```bash
env\Scripts\activate
```

**Mac/Linux:**

```bash
source env/bin/activate
```

---

### 4. Install dependencies

Jika sudah ada `requirements.txt`:

```bash
pip install -r requirements.txt
```

Jika belum ada:

```bash
pip install django
```

---

### 5. Masuk ke folder project Django (PENTING)

Kadang repo Django tidak langsung di root, biasanya ada folder seperti:

```bash
cd taskapp   # atau nama folder project Django di dalam repo
```

Contoh struktur:

```
TaskApp/
├── manage.py
├── taskapp/   ← ini folder project Django
├── app/
```

Jika file `manage.py` sudah ada di root, langkah ini dilewati.

---

### 6. Migrasi database

```bash
python manage.py makemigrations
python manage.py migrate
```

---

### 7. (Opsional) buat superuser admin

```bash
python manage.py createsuperuser
```

---

### 8. Jalankan server lokal

```bash
python manage.py runserver
```

---

### 9. Akses aplikasi

* App utama:
  [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

* Admin panel:
  [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## ⚠️ Catatan Penting (yang sering bikin error)

* Pastikan `manage.py` berada di direktori yang sedang kamu jalankan
* Jalankan semua command setelah virtual environment aktif
* Jika error module tidak ditemukan:

  ```bash
  pip install -r requirements.txt
  ```
* Jika error migration:

  ```bash
  python manage.py migrate --run-syncdb
  ```

---

