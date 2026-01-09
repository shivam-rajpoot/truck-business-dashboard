# Truck Business Dashboard

**Production-ready Truck Business Management System**  
Secure, persistent, and mobile-friendly dashboard for real-world truck business operations.

---

## 🚀 Features

### 🔐 Authentication & Security
- Owner and Driver login with **mobile number + password**
- Passwords **securely hashed** using bcrypt
- Role-based access control (Owner vs Driver)
- Session management for security

### 👑 Owner Dashboard
- **First-time setup** for Owner account
- Add, activate, and deactivate drivers
- View driver list with mobile numbers
- **Reports & Analytics**:
  - Date-range and month-wise profit
  - Driver-wise and truck-wise performance
  - Monthly comparison charts
  - Excel export of filtered data
- **Delete Data**:
  - Delete by specific date or month
  - Warning and backup recommendation before deletion

### 🚚 Driver Dashboard
- Add trip entries only
- Auto-capture driver identity
- Trip fields:
  - Date, Truck Number, From, To
  - Trip Rate, Diesel, Toll, Other Expenses
  - Auto-calculation of total expense and profit

### 💾 Storage
- SQLite database (`truck_business.db`) for persistent data
- Streamlit Cloud compatible for daily business use

### 📱 Mobile-Friendly
- Streamlit responsive UI
- Simple Hindi + English labels
- Easy navigation for drivers and owner

---

## 🖥️ First-Time Owner Setup
1. Open the app for the first time
2. If no Owner exists, setup screen will appear
3. Enter Name, Mobile Number (login ID), Password
4. After creation, login as Owner to manage drivers and trips

---

## 🗂️ Deployment Guide

1. Create a GitHub repository:
   ```text
   Repo Name: truck-business-dashboard
2.  Add files:
    ```text
     app.py (main code)
     requirements.txt
3. Go to Streamlit Cloud
4. Connect GitHub repository
5. Select app.py as main file and deploy
6. Open the app URL on desktop or mobile

📦 Requirements
streamlit
pandas
passlib[bcrypt]
openpyxl
