import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
from passlib.context import CryptContext

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(page_title="Truck Business Dashboard", layout="wide")
DB_NAME = "truck_business.db"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# =====================================================
# DATABASE
# =====================================================
def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        mobile TEXT UNIQUE,
        password_hash TEXT,
        role TEXT,
        active INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS trips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trip_date TEXT,
        truck_no TEXT,
        from_location TEXT,
        to_location TEXT,
        rate REAL,
        diesel REAL,
        toll REAL,
        other REAL,
        total_expense REAL,
        profit REAL,
        driver_mobile TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

init_db()

# =====================================================
# AUTH HELPERS
# =====================================================
def hash_password(password):
    return pwd_context.hash(password)

def verify_password(password, hashed):
    return pwd_context.verify(password, hashed)

def authenticate_user(mobile, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT mobile, password_hash, role, active FROM users WHERE mobile=?",
        (mobile,)
    )
    user = cur.fetchone()
    conn.close()

    if user and user[3] == 1 and verify_password(password, user[1]):
        return {"mobile": user[0], "role": user[2]}
    return None

# =====================================================
# OWNER EXIST CHECK (FIRST SETUP)
# =====================================================
def owner_exists():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE role='OWNER'")
    count = cur.fetchone()[0]
    conn.close()
    return count > 0

def first_owner_setup():
    st.title("🔐 First Time Setup – Create Owner")

    name = st.text_input("Owner Name")
    mobile = st.text_input("Mobile Number (Login ID)")
    pwd1 = st.text_input("Password", type="password")
    pwd2 = st.text_input("Confirm Password", type="password")

    if st.button("Create Owner Account"):
        if not name or not mobile or not pwd1:
            st.error("All fields required")
            return
        if pwd1 != pwd2:
            st.error("Passwords do not match")
            return

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (name, mobile, password_hash, role, active)
            VALUES (?,?,?,?,1)
        """, (name, mobile, hash_password(pwd1), "OWNER"))
        conn.commit()
        conn.close()

        st.success("Owner account created. Please login.")
        st.session_state.clear()
        st.rerun()

# =====================================================
# SECURITY GUARDS
# =====================================================
def require_login():
    if "user" not in st.session_state:
        st.stop()

def require_owner():
    require_login()
    if st.session_state.user["role"] != "OWNER":
        st.error("Owner access only")
        st.stop()

def require_driver():
    require_login()
    if st.session_state.user["role"] != "DRIVER":
        st.error("Driver access only")
        st.stop()

# =====================================================
# DRIVER DASHBOARD
# =====================================================
def driver_dashboard():
    require_driver()
    st.header("🚚 Driver Trip Entry")

    with st.form("trip_form"):
        trip_date = st.date_input("📅 Date", date.today())
        truck_no = st.text_input("🚛 Truck Number")
        frm = st.text_input("From (से)")
        to = st.text_input("To (तक)")
        rate = st.number_input("Trip Rate ₹", min_value=0.0)
        diesel = st.number_input("Diesel ₹", min_value=0.0)
        toll = st.number_input("Toll ₹", min_value=0.0)
        other = st.number_input("Other Expense ₹", min_value=0.0)

        if st.form_submit_button("Save Trip"):
            total = diesel + toll + other
            profit = rate - total

            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO trips
                (trip_date, truck_no, from_location, to_location,
                 rate, diesel, toll, other,
                 total_expense, profit, driver_mobile)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (
                trip_date, truck_no, frm, to,
                rate, diesel, toll, other,
                total, profit, st.session_state.user["mobile"]
            ))
            conn.commit()
            conn.close()

            st.success("✅ Trip Saved")

# =====================================================
# OWNER REPORTS + DELETE
# =====================================================
def owner_reports_and_delete():
    require_owner()

    conn = get_connection()
    df = pd.read_sql("SELECT * FROM trips", conn)
    conn.close()

    if df.empty:
        st.info("No data available")
        return

    df["trip_date"] = pd.to_datetime(df["trip_date"])
    df["month"] = df["trip_date"].dt.strftime("%Y-%m")

    st.subheader("📊 Reports")

    col1, col2 = st.columns(2)
    start = col1.date_input("From Date")
    end = col2.date_input("To Date")

    if start and end:
        df = df[(df["trip_date"] >= pd.to_datetime(start)) &
                (df["trip_date"] <= pd.to_datetime(end))]

    months = st.multiselect("Select Month", sorted(df["month"].unique()))
    if months:
        df = df[df["month"].isin(months)]

    st.metric("Total Profit ₹", round(df["profit"].sum(), 2))
    st.metric("Total Trips", len(df))

    st.markdown("### Driver-wise Profit")
    st.dataframe(df.groupby("driver_mobile")["profit"].sum().reset_index())

    st.markdown("### Truck-wise Profit")
    st.dataframe(df.groupby("truck_no")["profit"].sum().reset_index())

    st.markdown("### Monthly Comparison")
    st.bar_chart(df.groupby("month")["profit"].sum())

    st.download_button(
        "⬇️ Download Excel",
        df.to_excel(index=False),
        "profit_report.xlsx"
    )

    # ---------------- DELETE PANEL ----------------
    st.divider()
    st.markdown("## 🗑️ Delete Data (Owner Only)")
    st.warning("Deleted data cannot be recovered. Take backup first.")

    del_date = st.date_input("Delete Specific Date")
    if st.button("Delete Date Data"):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM trips WHERE trip_date=?", (str(del_date),))
        conn.commit()
        conn.close()
        st.success("Date data deleted")
        st.rerun()

    del_month = st.selectbox("Delete Month", sorted(df["month"].unique()))
    if st.button("Delete Month Data"):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM trips WHERE strftime('%Y-%m', trip_date)=?",
            (del_month,)
        )
        conn.commit()
        conn.close()
        st.success("Month data deleted")
        st.rerun()

# =====================================================
# OWNER DASHBOARD
# =====================================================
def owner_dashboard():
    require_owner()
    st.header("👑 Owner Dashboard")

    tab1, tab2 = st.tabs(["Driver Management", "Reports & Delete"])

    with tab1:
        st.subheader("➕ Add Driver")
        name = st.text_input("Driver Name")
        mobile = st.text_input("Mobile Number")
        password = st.text_input("Password", type="password")

        if st.button("Add Driver"):
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO users (name, mobile, password_hash, role, active)
                VALUES (?,?,?,?,1)
            """, (name, mobile, hash_password(password), "DRIVER"))
            conn.commit()
            conn.close()
            st.success("Driver added")

        conn = get_connection()
        df = pd.read_sql(
            "SELECT name, mobile, active FROM users WHERE role='DRIVER'",
            conn
        )
        conn.close()
        st.dataframe(df)

    with tab2:
        owner_reports_and_delete()

# =====================================================
# MAIN FLOW
# =====================================================
if not owner_exists():
    first_owner_setup()

elif "user" not in st.session_state:
    st.title("🔐 Login")

    mobile = st.text_input("Mobile Number")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = authenticate_user(mobile, password)
        if user:
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Invalid login")

else:
    if st.session_state.user["role"] == "OWNER":
        owner_dashboard()
    else:
        driver_dashboard()

    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()