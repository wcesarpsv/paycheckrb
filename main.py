import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime, date, time, timedelta
from pathlib import Path

DB_PATH = Path("employee_payroll.db")

# -----------------------------
# Database helpers
# -----------------------------
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        hourly_rate REAL NOT NULL,
        active INTEGER DEFAULT 1
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role_id INTEGER NOT NULL,
        is_admin INTEGER DEFAULT 0,
        active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(role_id) REFERENCES roles(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS time_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        work_date TEXT NOT NULL,
        check_in TEXT,
        check_out TEXT,
        hours_worked REAL DEFAULT 0,
        hourly_rate REAL NOT NULL,
        total_pay REAL DEFAULT 0,
        status TEXT DEFAULT 'OPEN',
        note TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(employee_id) REFERENCES employees(id)
    )
    """)

    conn.commit()

    # Default roles
    default_roles = [
        ("Ajudante", 20.0),
        ("Taper", 28.0),
        ("Drywall Nível 1", 25.0),
        ("Drywall Nível 2", 32.0),
    ]
    for name, rate in default_roles:
        cur.execute("INSERT OR IGNORE INTO roles (name, hourly_rate) VALUES (?, ?)", (name, rate))

    conn.commit()

    # Default admin
    cur.execute("SELECT id FROM roles WHERE name = ?", ("Drywall Nível 2",))
    role_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM employees WHERE email = ?", ("admin@app.com",))
    if cur.fetchone() is None:
        cur.execute("""
        INSERT INTO employees (name, email, password_hash, role_id, is_admin, active)
        VALUES (?, ?, ?, ?, 1, 1)
        """, ("Admin", "admin@app.com", hash_password("admin123"), role_id))

    conn.commit()
    conn.close()


def query_df(sql: str, params=()):
    conn = get_conn()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df


def execute(sql: str, params=()):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id


# -----------------------------
# Auth
# -----------------------------
def login(email: str, password: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    SELECT e.id, e.name, e.email, e.is_admin, e.active, r.name, r.hourly_rate, e.role_id
    FROM employees e
    JOIN roles r ON r.id = e.role_id
    WHERE e.email = ? AND e.password_hash = ?
    """, (email.lower().strip(), hash_password(password)))
    user = cur.fetchone()
    conn.close()

    if not user:
        return None
    if user[4] != 1:
        return None

    return {
        "id": user[0],
        "name": user[1],
        "email": user[2],
        "is_admin": bool(user[3]),
        "role": user[5],
        "hourly_rate": float(user[6]),
        "role_id": user[7],
    }


def require_login():
    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user is None:
        st.title("Controle de Funcionários")
        st.subheader("Login")
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar")

        if submitted:
            user = login(email, password)
            if user:
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Email ou senha inválidos, ou usuário inativo.")

        st.info("Login inicial do admin: admin@app.com / admin123")
        st.stop()


# -----------------------------
# Business logic
# -----------------------------
def get_roles(active_only=True):
    sql = "SELECT id, name, hourly_rate, active FROM roles"
    if active_only:
        sql += " WHERE active = 1"
    sql += " ORDER BY name"
    return query_df(sql)


def get_employees(active_only=False):
    sql = """
    SELECT e.id, e.name, e.email, r.name AS role, r.hourly_rate, e.is_admin, e.active
    FROM employees e
    JOIN roles r ON r.id = e.role_id
    """
    if active_only:
        sql += " WHERE e.active = 1"
    sql += " ORDER BY e.name"
    return query_df(sql)


def get_open_entry(employee_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    SELECT id, check_in, work_date, hourly_rate
    FROM time_entries
    WHERE employee_id = ? AND status = 'OPEN'
    ORDER BY id DESC
    LIMIT 1
    """, (employee_id,))
    row = cur.fetchone()
    conn.close()
    return row


def check_in(employee_id: int, hourly_rate: float, note: str = ""):
    open_entry = get_open_entry(employee_id)
    if open_entry:
        return False, "Você já tem um check-in aberto. Finalize antes de iniciar outro."

    now = datetime.now()
    execute("""
    INSERT INTO time_entries (employee_id, work_date, check_in, hourly_rate, status, note)
    VALUES (?, ?, ?, ?, 'OPEN', ?)
    """, (employee_id, now.date().isoformat(), now.isoformat(timespec="seconds"), hourly_rate, note))
    return True, "Check-in registrado com sucesso."


def check_out(employee_id: int):
    open_entry = get_open_entry(employee_id)
    if not open_entry:
        return False, "Nenhum check-in aberto encontrado."

    entry_id, check_in_str, work_date, hourly_rate = open_entry
    now = datetime.now()
    check_in_dt = datetime.fromisoformat(check_in_str)
    hours = round((now - check_in_dt).total_seconds() / 3600, 2)
    total_pay = round(hours * float(hourly_rate), 2)

    execute("""
    UPDATE time_entries
    SET check_out = ?, hours_worked = ?, total_pay = ?, status = 'CLOSED', updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (now.isoformat(timespec="seconds"), hours, total_pay, entry_id))

    return True, f"Check-out registrado. Horas: {hours:.2f} | Total: ${total_pay:.2f}"


def payroll_report(start_date, end_date):
    return query_df("""
    SELECT
        e.name AS Funcionario,
        r.name AS Classificacao,
        COUNT(t.id) AS Dias_Trabalhados,
        ROUND(SUM(t.hours_worked), 2) AS Horas_Total,
        ROUND(AVG(t.hourly_rate), 2) AS Valor_Hora_Medio,
        ROUND(SUM(t.total_pay), 2) AS Total_Pagar
    FROM time_entries t
    JOIN employees e ON e.id = t.employee_id
    JOIN roles r ON r.id = e.role_id
    WHERE t.status = 'CLOSED'
      AND date(t.work_date) BETWEEN date(?) AND date(?)
    GROUP BY e.id, e.name, r.name
    ORDER BY Total_Pagar DESC
    """, (start_date.isoformat(), end_date.isoformat()))


def detailed_entries(start_date, end_date):
    return query_df("""
    SELECT
        t.id,
        e.name AS Funcionario,
        r.name AS Classificacao,
        t.work_date AS Data,
        t.check_in AS Entrada,
        t.check_out AS Saida,
        ROUND(t.hours_worked, 2) AS Horas,
        ROUND(t.hourly_rate, 2) AS Valor_Hora,
        ROUND(t.total_pay, 2) AS Total_Dia,
        t.status AS Status,
        t.note AS Observacao
    FROM time_entries t
    JOIN employees e ON e.id = t.employee_id
    JOIN roles r ON r.id = e.role_id
    WHERE date(t.work_date) BETWEEN date(?) AND date(?)
    ORDER BY t.work_date DESC, e.name
    """, (start_date.isoformat(), end_date.isoformat()))


# -----------------------------
# Pages
# -----------------------------
def page_employee_clock():
    user = st.session_state.user
    st.title("Ponto do Funcionário")
    st.write(f"Funcionário: **{user['name']}**")
    st.write(f"Classificação: **{user['role']}** | Valor/hora: **${user['hourly_rate']:.2f}**")

    open_entry = get_open_entry(user["id"])

    if open_entry:
        entry_id, check_in_str, work_date, hourly_rate = open_entry
        check_in_dt = datetime.fromisoformat(check_in_str)
        current_hours = round((datetime.now() - check_in_dt).total_seconds() / 3600, 2)
        st.warning(f"Check-in aberto desde {check_in_dt.strftime('%Y-%m-%d %H:%M:%S')}. Horas até agora: {current_hours:.2f}")
        if st.button("Finalizar trabalho / Check-out", type="primary"):
            ok, msg = check_out(user["id"])
            if ok:
                st.success(msg)
            else:
                st.error(msg)
            st.rerun()
    else:
        note = st.text_area("Observação opcional", placeholder="Ex: job site, endereço, tarefa do dia...")
        if st.button("Começar trabalho / Check-in", type="primary"):
            ok, msg = check_in(user["id"], user["hourly_rate"], note)
            if ok:
                st.success(msg)
            else:
                st.error(msg)
            st.rerun()

    st.divider()
    st.subheader("Meus últimos registros")
    df = query_df("""
    SELECT work_date AS Data, check_in AS Entrada, check_out AS Saida,
           ROUND(hours_worked, 2) AS Horas, ROUND(total_pay, 2) AS Total, status AS Status, note AS Observacao
    FROM time_entries
    WHERE employee_id = ?
    ORDER BY id DESC
    LIMIT 20
    """, (user["id"],))
    st.dataframe(df, use_container_width=True)


def page_admin_dashboard():
    st.title("Painel Admin")

    today = date.today()
    start_week = today - timedelta(days=today.weekday())
    end_week = start_week + timedelta(days=6)

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Data inicial", value=start_week)
    with col2:
        end_date = st.date_input("Data final", value=end_week)

    report = payroll_report(start_date, end_date)
    details = detailed_entries(start_date, end_date)

    total_pay = report["Total_Pagar"].sum() if not report.empty else 0
    total_hours = report["Horas_Total"].sum() if not report.empty else 0
    total_workers = report["Funcionario"].nunique() if not report.empty else 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Total a pagar", f"${total_pay:,.2f}")
    m2.metric("Total de horas", f"{total_hours:,.2f}h")
    m3.metric("Funcionários no período", total_workers)

    st.subheader("Resumo de pagamento")
    st.dataframe(report, use_container_width=True)

    if not report.empty:
        csv = report.to_csv(index=False).encode("utf-8")
        st.download_button("Baixar resumo em CSV", csv, "resumo_pagamento.csv", "text/csv")

    st.subheader("Registros detalhados")
    st.dataframe(details, use_container_width=True)

    if not details.empty:
        csv_details = details.to_csv(index=False).encode("utf-8")
        st.download_button("Baixar detalhes em CSV", csv_details, "detalhes_ponto.csv", "text/csv")


def page_manage_roles():
    st.title("Classificações e valores por hora")

    with st.form("new_role"):
        name = st.text_input("Nome da classificação", placeholder="Ex: Drywall Nível 3")
        hourly_rate = st.number_input("Valor por hora", min_value=0.0, step=1.0, value=25.0)
        submitted = st.form_submit_button("Cadastrar classificação")

    if submitted:
        try:
            execute("INSERT INTO roles (name, hourly_rate, active) VALUES (?, ?, 1)", (name.strip(), hourly_rate))
            st.success("Classificação cadastrada.")
            st.rerun()
        except sqlite3.IntegrityError:
            st.error("Essa classificação já existe.")

    st.subheader("Classificações cadastradas")
    roles = get_roles(active_only=False)
    st.dataframe(roles, use_container_width=True)

    st.subheader("Editar valor/hora")
    if not roles.empty:
        role_map = {f"{row['name']} - ${row['hourly_rate']:.2f}/h": int(row["id"]) for _, row in roles.iterrows()}
        selected = st.selectbox("Selecione", list(role_map.keys()))
        new_rate = st.number_input("Novo valor por hora", min_value=0.0, step=1.0, value=25.0, key="edit_rate")
        active = st.checkbox("Ativo", value=True)
        if st.button("Salvar alteração"):
            execute("UPDATE roles SET hourly_rate = ?, active = ? WHERE id = ?", (new_rate, int(active), role_map[selected]))
            st.success("Classificação atualizada.")
            st.rerun()


def page_manage_employees():
    st.title("Funcionários")

    roles = get_roles(active_only=True)
    if roles.empty:
        st.error("Cadastre uma classificação antes de cadastrar funcionários.")
        return

    role_options = {f"{row['name']} - ${row['hourly_rate']:.2f}/h": int(row["id"]) for _, row in roles.iterrows()}

    with st.form("new_employee"):
        name = st.text_input("Nome")
        email = st.text_input("Email/login")
        password = st.text_input("Senha inicial", type="password")
        role_label = st.selectbox("Classificação", list(role_options.keys()))
        is_admin = st.checkbox("É admin?")
        submitted = st.form_submit_button("Cadastrar funcionário")

    if submitted:
        if not name or not email or not password:
            st.error("Preencha nome, email e senha.")
        else:
            try:
                execute("""
                INSERT INTO employees (name, email, password_hash, role_id, is_admin, active)
                VALUES (?, ?, ?, ?, ?, 1)
                """, (name.strip(), email.lower().strip(), hash_password(password), role_options[role_label], int(is_admin)))
                st.success("Funcionário cadastrado.")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Já existe funcionário com esse email.")

    st.subheader("Funcionários cadastrados")
    employees = get_employees(active_only=False)
    st.dataframe(employees, use_container_width=True)

    st.subheader("Editar funcionário")
    if not employees.empty:
        emp_map = {f"{row['name']} - {row['email']}": int(row["id"]) for _, row in employees.iterrows()}
        selected_emp = st.selectbox("Selecione funcionário", list(emp_map.keys()))
        new_role_label = st.selectbox("Nova classificação", list(role_options.keys()), key="emp_role_edit")
        active = st.checkbox("Funcionário ativo", value=True, key="emp_active")
        admin = st.checkbox("Admin", value=False, key="emp_admin")
        new_password = st.text_input("Nova senha opcional", type="password")

        if st.button("Salvar funcionário"):
            emp_id = emp_map[selected_emp]
            execute("UPDATE employees SET role_id = ?, active = ?, is_admin = ? WHERE id = ?",
                    (role_options[new_role_label], int(active), int(admin), emp_id))
            if new_password:
                execute("UPDATE employees SET password_hash = ? WHERE id = ?", (hash_password(new_password), emp_id))
            st.success("Funcionário atualizado.")
            st.rerun()


def page_manual_adjustments():
    st.title("Correção manual de ponto")
    st.warning("Use essa área para corrigir esquecimentos de check-in/check-out ou lançar horas manualmente.")

    employees = get_employees(active_only=True)
    if employees.empty:
        st.error("Nenhum funcionário ativo.")
        return

    emp_options = {f"{row['name']} - {row['role']} - ${row['hourly_rate']:.2f}/h": row for _, row in employees.iterrows()}

    with st.form("manual_entry"):
        emp_label = st.selectbox("Funcionário", list(emp_options.keys()))
        work_date = st.date_input("Data", value=date.today())
        check_in_time = st.time_input("Hora de entrada", value=time(8, 0))
        check_out_time = st.time_input("Hora de saída", value=time(17, 0))
        note = st.text_area("Observação")
        submitted = st.form_submit_button("Salvar registro manual")

    if submitted:
        emp = emp_options[emp_label]
        in_dt = datetime.combine(work_date, check_in_time)
        out_dt = datetime.combine(work_date, check_out_time)
        if out_dt <= in_dt:
            st.error("A saída precisa ser depois da entrada.")
        else:
            hours = round((out_dt - in_dt).total_seconds() / 3600, 2)
            hourly_rate = float(emp["hourly_rate"])
            total = round(hours * hourly_rate, 2)
            execute("""
            INSERT INTO time_entries (employee_id, work_date, check_in, check_out, hours_worked, hourly_rate, total_pay, status, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'CLOSED', ?)
            """, (int(emp["id"]), work_date.isoformat(), in_dt.isoformat(timespec="seconds"), out_dt.isoformat(timespec="seconds"), hours, hourly_rate, total, note))
            st.success(f"Registro salvo: {hours:.2f}h | Total: ${total:.2f}")
            st.rerun()


# -----------------------------
# App
# -----------------------------
def main():
    st.set_page_config(page_title="Controle de Funcionários", layout="wide")
    init_db()
    require_login()

    user = st.session_state.user

    with st.sidebar:
        st.write(f"Logado como: **{user['name']}**")
        st.write("Admin" if user["is_admin"] else "Funcionário")
        if st.button("Sair"):
            st.session_state.user = None
            st.rerun()

        if user["is_admin"]:
            page = st.radio("Menu", [
                "Painel Admin",
                "Ponto do Funcionário",
                "Funcionários",
                "Classificações",
                "Correção Manual"
            ])
        else:
            page = "Ponto do Funcionário"

    if page == "Painel Admin":
        page_admin_dashboard()
    elif page == "Ponto do Funcionário":
        page_employee_clock()
    elif page == "Funcionários":
        page_manage_employees()
    elif page == "Classificações":
        page_manage_roles()
    elif page == "Correção Manual":
        page_manual_adjustments()


if __name__ == "__main__":
    main()
