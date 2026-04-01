---

# 🎓 Online Student Marksheet Generation & Distribution System (MGDM)

A web-based platform to **automate marksheet generation, management, and distribution** for educational institutions.

This project replaces traditional manual result handling with a **secure, scalable, and role-based system** built using Django and MariaDB.

---

## 🚀 Features

### 👨‍💼 Admin

* Bulk upload of students and subjects via spreadsheets
* Manage departments, courses, and users
* Review and publish marksheets
* Full system control

### 👨‍🏫 Teacher

* Upload marks using Excel/ODS templates
* View and edit submitted marks
* Manage assigned subjects/tests

### 🎓 Student

* Secure login access
* View semester-wise results
* Download marksheets as **PDF**
* 24×7 availability

---

## 🧠 Key Highlights

* 📊 Automated **SGPA/CGPA calculation**
* 📁 Bulk data upload using spreadsheets
* 📄 Dynamic **PDF generation** (ReportLab)
* 🔐 Role-based authentication system
* 📌 QR codes for marksheet verification
* 🏗️ Built on Django MVT architecture

---

## 🛠️ Tech Stack

| Category  | Technology                             |
| --------- | -------------------------------------- |
| Language  | Python                                 |
| Backend   | Django                                 |
| Database  | MariaDB                                |
| Frontend  | HTML, CSS, JavaScript                  |
| Libraries | pandas, reportlab, qrcode, mysqlclient |

---

## 🏗️ System Architecture

The project follows Django’s **MVT (Model-View-Template)** architecture:

* **Models** → Database schema & structure
* **Views** → Business logic & request handling
* **Templates** → UI rendering

---

## 📂 Modules

### 🔐 Authentication Module

* Login, logout, session handling
* Role-based access control

### 🛠️ Admin Module

* Bulk upload (students & subjects)
* Marksheet publishing workflow

### 📊 Teacher Module

* Upload and manage marks
* Spreadsheet-based data handling

### 📄 Student Module

* View results
* Download marksheets

### 🧮 Marksheet Generation Module

* Grade calculation
* SGPA/CGPA computation
* PDF generation with QR & watermark

---

## ⚙️ Installation & Setup

```bash
# Clone the repository
git clone https://github.com/your-username/mgdm-system.git
cd mgdm-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # (Linux/macOS)
venv\Scripts\activate     # (Windows)

# Install dependencies
pip install -r requirements.txt

# Configure database (MariaDB)
# Update settings.py with your DB credentials

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver
```

---

## 📸 Screenshots

* Admin Dashboard
* Teacher Mark Upload Interface
* Student Marksheet View
* Generated PDF Marksheet

*(Add screenshots here for better presentation)*

---

## 🎯 Problem Solved

Traditional systems suffer from:

* ❌ Manual errors
* ⏳ Delays in result publication
* 📂 Scattered data
* 🚫 Limited accessibility

✅ This system provides:

* Centralized data management
* Automated processing
* Secure and instant access

---

## 🔮 Future Scope

* 📷 OCR-based data entry (scan handwritten/printed marks)
* 🔑 Password recovery via email
* 🔗 Integration with other institutional systems (APIs)
* 📱 Mobile app support

---

## 📚 References

* Django Documentation
* ReportLab Documentation
* Pandas Documentation
* Database System Concepts (Silberschatz)

---

## 👨‍💻 Author

**Yash Gupta**
B.Tech CSE, NIT Sikkim
Roll No: B230038CS

---

## 📄 License

This project is for academic purposes. You may modify and use it with proper attribution.

---
