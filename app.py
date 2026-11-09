
from flask import Flask, request, redirect, url_for, flash, render_template_string
from database import get_db_connection
from datetime import date
from decimal import Decimal
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
app.secret_key = "home-budget-secret-key"


# -------------------- DATABASE HELPERS --------------------

def query_db(sql, values=(), fetch=True):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, values)

    result = cursor.fetchall() if fetch else None

    conn.commit()
    cursor.close()
    conn.close()
    return result


def get_categories(category_type=None):
    if category_type:
        return query_db(
            "SELECT * FROM categories WHERE category_type=%s ORDER BY category_name",
            (category_type,)
        )
    return query_db("SELECT * FROM categories ORDER BY category_name")


def money(value):
    return float(value or 0)


# -------------------- COMMON WEBSITE DESIGN --------------------

BASE = """
<!DOCTYPE html>
<html>
<head>
    <title>Home Budget Manager</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f4f6fb;
            color: #20263a;
        }
        .sidebar {
            width: 230px;
            height: 100vh;
            position: fixed;
            left: 0;
            top: 0;
            background: #17233d;
            color: white;
            padding: 25px 15px;
        }
        .brand { font-size: 21px; font-weight: bold; margin: 0 0 35px 10px; }
        .sidebar a {
            display: block;
            color: #dce4f5;
            padding: 13px;
            text-decoration: none;
            border-radius: 8px;
            margin-bottom: 8px;
        }
        .sidebar a:hover { background: #304362; color: white; }
        .main { margin-left: 230px; padding: 30px; }
        h1 { margin-top: 0; font-size: 27px; }
        .subtitle { color: #788196; margin-bottom: 25px; }
        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 18px;
            margin-bottom: 25px;
        }
        .card {
            background: white;
            border-radius: 12px;
            padding: 22px;
            box-shadow: 0 3px 12px #17233d0d;
        }
        .card p { color: #778096; margin: 0 0 12px; }
        .amount { font-size: 25px; font-weight: bold; }
        .green { color: #159568; }
        .red { color: #e05252; }
        .blue { color: #4169d8; }
        .panel {
            background: white;
            padding: 22px;
            border-radius: 12px;
            margin-bottom: 22px;
            box-shadow: 0 3px 12px #17233d0d;
            overflow-x: auto;
        }
        table { width: 100%; border-collapse: collapse; min-width: 600px; }
        th, td { padding: 13px; text-align: left; border-bottom: 1px solid #edf0f5; }
        th { color: #758097; font-size: 13px; }
        input, select, textarea {
            width: 100%;
            padding: 12px;
            margin: 7px 0 17px;
            border: 1px solid #dce1eb;
            border-radius: 7px;
            font-size: 14px;
        }
        label { font-weight: bold; font-size: 14px; }
        button, .btn {
            display: inline-block;
            background: #4169d8;
            color: white;
            border: none;
            border-radius: 7px;
            padding: 11px 17px;
            cursor: pointer;
            text-decoration: none;
            font-size: 14px;
        }
        .btn-danger { background: #e05252; }
        .btn-light { background: #e9efff; color: #3158c6; }
        .actions { display: flex; gap: 7px; }
        .flash {
            background: #e5f7ed;
            color: #14794b;
            padding: 12px;
            border-radius: 7px;
            margin-bottom: 18px;
        }
        .form-box { max-width: 650px; }
        .progress {
            height: 10px;
            background: #edf0f5;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 10px;
        }
        .progress div { height: 100%; background: #4169d8; }
        .empty { color: #8a91a2; padding: 20px 0; }
        img.chart { max-width: 100%; height: auto; }
        @media(max-width: 700px) {
            .sidebar { width: 100%; height: auto; position: relative; padding: 12px; }
            .brand { margin: 5px 5px 12px; }
            .sidebar a { display: inline-block; padding: 9px; margin: 2px; }
            .main { margin-left: 0; padding: 18px; }
        }
    </style>
</head>
<body>
<div class="sidebar">
    <div class="brand">💰 Home Budget</div>
    <a href="/">📊 Dashboard</a>
    <a href="/transactions">💳 Transactions</a>
    <a href="/add-transaction">➕ Add Transaction</a>
    <a href="/budgets">🎯 Monthly Budgets</a>
    <a href="/reports">📈 Reports & Analysis</a>
</div>
<div class="main">
    {% with messages = get_flashed_messages() %}
        {% for message in messages %}
            <div class="flash">{{ message }}</div>
        {% endfor %}
    {% endwith %}
    {{ content|safe }}
</div>
</body>
</html>
"""


def page(content, **kwargs):
    body = render_template_string(content, **kwargs)
    return render_template_string(BASE, content=body)


# -------------------- DASHBOARD --------------------

@app.route("/")
def dashboard():
    today = date.today()

    totals = query_db("""
        SELECT
            COALESCE(SUM(CASE WHEN transaction_type='Income' THEN amount ELSE 0 END),0) AS income,
            COALESCE(SUM(CASE WHEN transaction_type='Expense' THEN amount ELSE 0 END),0) AS expenses
        FROM transactions
        WHERE MONTH(transaction_date)=%s AND YEAR(transaction_date)=%s
    """, (today.month, today.year))[0]

    income = money(totals["income"])
    expenses = money(totals["expenses"])
    savings = income - expenses

    recent = query_db("""
        SELECT t.*, c.category_name
        FROM transactions t
        LEFT JOIN categories c ON t.category_id=c.category_id
        ORDER BY t.transaction_date DESC, t.transaction_id DESC
        LIMIT 7
    """)

    content = """
    <h1>Dashboard</h1>
    <p class="subtitle">Your financial overview for {{ month }}</p>

    <div class="cards">
        <div class="card"><p>Total Income</p>
            <div class="amount green">₹{{ "%.2f"|format(income) }}</div></div>
        <div class="card"><p>Total Expenses</p>
            <div class="amount red">₹{{ "%.2f"|format(expenses) }}</div></div>
        <div class="card"><p>Net Savings</p>
            <div class="amount blue">₹{{ "%.2f"|format(savings) }}</div></div>
    </div>

    <div class="panel">
        <h3>Recent Transactions</h3>
        {% if recent %}
        <table>
            <tr><th>Date</th><th>Description</th><th>Category</th>
            <th>Type</th><th>Amount</th></tr>
            {% for t in recent %}
            <tr>
                <td>{{ t.transaction_date }}</td>
                <td>{{ t.description or '-' }}</td>
                <td>{{ t.category_name or '-' }}</td>
                <td>{{ t.transaction_type }}</td>
                <td>₹{{ "%.2f"|format(t.amount|float) }}</td>
            </tr>
            {% endfor %}
        </table>
        {% else %}
        <p class="empty">No transactions yet. Add your first transaction!</p>
        {% endif %}
        <br><a class="btn" href="/add-transaction">Add Transaction</a>
    </div>
    """
    return page(
        content,
        income=income,
        expenses=expenses,
        savings=savings,
        recent=recent,
        month=today.strftime("%B %Y")
    )


# -------------------- TRANSACTIONS --------------------

@app.route("/transactions")
def transactions():
    records = query_db("""
        SELECT t.*, c.category_name
        FROM transactions t
        LEFT JOIN categories c ON t.category_id=c.category_id
        ORDER BY t.transaction_date DESC, t.transaction_id DESC
    """)

    content = """
    <h1>Transactions</h1>
    <p class="subtitle">View and manage your income and expenses.</p>
    <div class="panel">
        <a class="btn" href="/add-transaction">+ Add Transaction</a>
        <br><br>
        {% if records %}
        <table>
            <tr><th>Date</th><th>Description</th><th>Category</th>
            <th>Type</th><th>Amount</th><th>Actions</th></tr>
            {% for t in records %}
            <tr>
                <td>{{ t.transaction_date }}</td>
                <td>{{ t.description or '-' }}</td>
                <td>{{ t.category_name or '-' }}</td>
                <td>{{ t.transaction_type }}</td>
                <td>₹{{ "%.2f"|format(t.amount|float) }}</td>
                <td><div class="actions">
                    <a class="btn btn-light" href="/edit-transaction/{{ t.transaction_id }}">Edit</a>
                    <form method="POST" action="/delete-transaction/{{ t.transaction_id }}"
                     onsubmit="return confirm('Delete this transaction?')" style="margin:0">
                        <button class="btn-danger">Delete</button>
                    </form>
                </div></td>
            </tr>
            {% endfor %}
        </table>
        {% else %}
        <p class="empty">No transactions found.</p>
        {% endif %}
    </div>
    """
    return page(content, records=records)


FORM_TEMPLATE = """
<h1>{{ heading }}</h1>
<p class="subtitle">Enter the transaction details below.</p>
<div class="panel form-box">
<form method="POST">
    <label>Transaction Type</label>
    <select name="transaction_type" id="type" required>
        <option value="Income" {% if selected_type=='Income' %}selected{% endif %}>Income</option>
        <option value="Expense" {% if selected_type=='Expense' %}selected{% endif %}>Expense</option>
    </select>

    <label>Category</label>
    <select name="category_id" id="category" required>
        {% for c in categories %}
        <option value="{{ c.category_id }}"
        {% if selected_category|string == c.category_id|string %}selected{% endif %}>
            {{ c.category_name }}
        </option>
        {% endfor %}
    </select>

    <label>Amount (₹)</label>
    <input type="number" name="amount" step="0.01" min="0.01"
           value="{{ amount }}" placeholder="Enter amount" required>

    <label>Date</label>
    <input type="date" name="transaction_date" value="{{ transaction_date }}" required>

    <label>Description</label>
    <textarea name="description" rows="3" placeholder="Enter description">{{ description }}</textarea>

    <button type="submit">{{ button_text }}</button>
    <a class="btn btn-light" href="/transactions">Cancel</a>
</form>
</div>

<script>
const allCategories = {{ all_categories|tojson }};
const categorySelect = document.getElementById("category");
const typeSelect = document.getElementById("type");
const selectedCategory = "{{ selected_category }}";

function filterCategories() {
    const type = typeSelect.value;
    const oldValue = categorySelect.value;
    categorySelect.innerHTML = "";

    allCategories.filter(c => c.category_type === type).forEach(c => {
        const option = document.createElement("option");
        option.value = c.category_id;
        option.textContent = c.category_name;
        categorySelect.appendChild(option);
    });

    if ([...categorySelect.options].some(o => o.value === oldValue)) {
        categorySelect.value = oldValue;
    } else if ([...categorySelect.options].some(o => o.value === selectedCategory)) {
        categorySelect.value = selectedCategory;
    }
}
typeSelect.addEventListener("change", filterCategories);
filterCategories();
</script>
"""


def save_transaction_form(transaction_id=None):
    if request.method == "POST":
        transaction_type = request.form.get("transaction_type")
        category_id = request.form.get("category_id")
        amount = request.form.get("amount")
        transaction_date = request.form.get("transaction_date")
        description = request.form.get("description", "").strip()

        if transaction_type not in ("Income", "Expense"):
            flash("Invalid transaction type.")
            return redirect(request.url)

        try:
            amount_value = Decimal(amount)
            if amount_value <= 0:
                raise ValueError()
        except Exception:
            flash("Enter a valid amount greater than zero.")
            return redirect(request.url)

        category = query_db(
            "SELECT * FROM categories WHERE category_id=%s AND category_type=%s",
            (category_id, transaction_type)
        )

        if not category:
            flash("Please select a valid category.")
            return redirect(request.url)

        if transaction_id:
            query_db("""
                UPDATE transactions
                SET transaction_date=%s, transaction_type=%s,
                    category_id=%s, amount=%s, description=%s
                WHERE transaction_id=%s
            """, (transaction_date, transaction_type, category_id,
                  amount_value, description, transaction_id), fetch=False)
            flash("Transaction updated successfully!")
        else:
            query_db("""
                INSERT INTO transactions
                (transaction_date, transaction_type, category_id, amount, description)
                VALUES (%s,%s,%s,%s,%s)
            """, (transaction_date, transaction_type, category_id,
                  amount_value, description), fetch=False)
            flash("Transaction added successfully!")

        return redirect(url_for("transactions"))

    all_categories = get_categories()
    selected_type = "Expense"
    selected_category = ""
    amount = ""
    transaction_date = date.today().isoformat()
    description = ""
    heading = "Add Transaction"
    button_text = "Save Transaction"

    if transaction_id:
        record = query_db(
            "SELECT * FROM transactions WHERE transaction_id=%s",
            (transaction_id,)
        )
        if not record:
            flash("Transaction not found.")
            return redirect(url_for("transactions"))

        record = record[0]
        selected_type = record["transaction_type"]
        selected_category = record["category_id"]
        amount = record["amount"]
        transaction_date = record["transaction_date"].isoformat()
        description = record["description"] or ""
        heading = "Edit Transaction"
        button_text = "Update Transaction"

    return page(
        FORM_TEMPLATE,
        heading=heading,
        button_text=button_text,
        categories=get_categories(selected_type),
        all_categories=all_categories,
        selected_type=selected_type,
        selected_category=selected_category,
        amount=amount,
        transaction_date=transaction_date,
        description=description
    )


@app.route("/add-transaction", methods=["GET", "POST"])
def add_transaction():
    return save_transaction_form()


@app.route("/edit-transaction/<int:transaction_id>", methods=["GET", "POST"])
def edit_transaction(transaction_id):
    return save_transaction_form(transaction_id)


@app.route("/delete-transaction/<int:transaction_id>", methods=["POST"])
def delete_transaction(transaction_id):
    query_db(
        "DELETE FROM transactions WHERE transaction_id=%s",
        (transaction_id,),
        fetch=False
    )
    flash("Transaction deleted successfully!")
    return redirect(url_for("transactions"))


# -------------------- MONTHLY BUDGETS --------------------

@app.route("/budgets", methods=["GET", "POST"])
def budgets():
    today = date.today()

    if request.method == "POST":
        category_id = request.form.get("category_id")
        budget_amount = request.form.get("budget_amount")
        month = request.form.get("budget_month")
        year = request.form.get("budget_year")

        try:
            value = Decimal(budget_amount)
            if value <= 0:
                raise ValueError()
        except Exception:
            flash("Enter a valid budget amount.")
            return redirect(url_for("budgets"))

        category = query_db(
            "SELECT * FROM categories WHERE category_id=%s AND category_type='Expense'",
            (category_id,)
        )
        if not category:
            flash("Select a valid expense category.")
            return redirect(url_for("budgets"))

        query_db("""
            INSERT INTO monthly_budgets
            (category_id, budget_month, budget_year, budget_amount)
            VALUES (%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE budget_amount=VALUES(budget_amount)
        """, (category_id, month, year, value), fetch=False)

        flash("Budget saved successfully!")
        return redirect(url_for("budgets"))

    rows = query_db("""
        SELECT b.*, c.category_name,
        COALESCE((
            SELECT SUM(t.amount) FROM transactions t
            WHERE t.category_id=b.category_id
            AND t.transaction_type='Expense'
            AND MONTH(t.transaction_date)=b.budget_month
            AND YEAR(t.transaction_date)=b.budget_year
        ),0) AS spent
        FROM monthly_budgets b
        JOIN categories c ON b.category_id=c.category_id
        ORDER BY b.budget_year DESC, b.budget_month DESC
    """)

    content = """
    <h1>Monthly Budgets</h1>
    <p class="subtitle">Set spending limits and track your expenses.</p>

    <div class="panel form-box">
        <h3>Set a Budget</h3>
        <form method="POST">
            <label>Expense Category</label>
            <select name="category_id" required>
                {% for c in categories %}
                <option value="{{ c.category_id }}">{{ c.category_name }}</option>
                {% endfor %}
            </select>
            <label>Budget Amount (₹)</label>
            <input type="number" name="budget_amount" min="0.01" step="0.01" required>
            <label>Month</label>
            <select name="budget_month">
                {% for m in range(1,13) %}
                <option value="{{ m }}" {% if m==month %}selected{% endif %}>
                    {{ month_names[m-1] }}
                </option>
                {% endfor %}
            </select>
            <label>Year</label>
            <input type="number" name="budget_year" value="{{ year }}" required>
            <button type="submit">Save Budget</button>
        </form>
    </div>

    <div class="panel">
        <h3>Budget Overview</h3>
        {% if rows %}
        {% for b in rows %}
            {% set spent = b.spent|float %}
            {% set limit = b.budget_amount|float %}
            {% set percent = (spent / limit * 100) if limit else 0 %}
            <p><b>{{ b.category_name }}</b> —
            {{ month_names[b.budget_month-1] }} {{ b.budget_year }}</p>
            <p>Spent: ₹{{ "%.2f"|format(spent) }} /
               Budget: ₹{{ "%.2f"|format(limit) }}</p>
            <div class="progress">
                <div style="width:{{ [percent,100]|min }}%;
                    background:{{ '#e05252' if percent>100 else '#4169d8' }}"></div>
            </div>
            <p style="color:{{ '#e05252' if percent>100 else '#159568' }}">
                {% if percent>100 %}Budget exceeded!{% else %}
                Remaining: ₹{{ "%.2f"|format(limit-spent) }}{% endif %}
            </p>
            <hr>
        {% endfor %}
        {% else %}
        <p class="empty">No budgets created yet.</p>
        {% endif %}
    </div>
    """
    import calendar
    return page(
        content,
        categories=get_categories("Expense"),
        rows=rows,
        month=today.month,
        year=today.year,
        month_names=list(calendar.month_name)[1:]
    )


# -------------------- REPORTS AND CHARTS --------------------

@app.route("/reports")
def reports():
    records = query_db("""
        SELECT transaction_date, transaction_type, amount, category_id
        FROM transactions
        ORDER BY transaction_date
    """)

    if records:
        df = pd.DataFrame(records)
        df["transaction_date"] = pd.to_datetime(df["transaction_date"])
        df["amount"] = pd.to_numeric(df["amount"])
        df["month"] = df["transaction_date"].dt.strftime("%b %Y")

        monthly = df.groupby(["month", "transaction_type"])["amount"].sum().unstack(fill_value=0)

        for col in ["Income", "Expense"]:
            if col not in monthly.columns:
                monthly[col] = 0

        monthly["Savings"] = monthly["Income"] - monthly["Expense"]
        monthly = monthly.tail(12)

        chart_data = monthly[["Income", "Expense"]]

        fig, ax = plt.subplots(figsize=(9, 4))
        chart_data.plot(kind="bar", ax=ax)
        ax.set_title("Monthly Income vs Expenses")
        ax.set_ylabel("Amount (₹)")
        ax.set_xlabel("Month")
        plt.xticks(rotation=35, ha="right")
        plt.tight_layout()

        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=110)
        buffer.seek(0)
        chart = base64.b64encode(buffer.read()).decode("utf-8")
        plt.close(fig)

        income = money(df.loc[df.transaction_type == "Income", "amount"].sum())
        expenses = money(df.loc[df.transaction_type == "Expense", "amount"].sum())
        savings = income - expenses

        category_records = query_db("""
            SELECT c.category_name, SUM(t.amount) AS total
            FROM transactions t
            JOIN categories c ON t.category_id=c.category_id
            WHERE t.transaction_type='Expense'
            GROUP BY c.category_name
            ORDER BY total DESC
        """)
    else:
        chart = None
        income = expenses = savings = 0
        category_records = []

    content = """
    <h1>Reports & Analysis</h1>
    <p class="subtitle">Understand your financial performance.</p>

    <div class="cards">
        <div class="card"><p>Total Income</p>
            <div class="amount green">₹{{ "%.2f"|format(income) }}</div></div>
        <div class="card"><p>Total Expenses</p>
            <div class="amount red">₹{{ "%.2f"|format(expenses) }}</div></div>
        <div class="card"><p>Overall Savings</p>
            <div class="amount blue">₹{{ "%.2f"|format(savings) }}</div></div>
    </div>

    <div class="panel">
        <h3>Monthly Income vs Expenses</h3>
        {% if chart %}
            <img class="chart" src="data:image/png;base64,{{ chart }}">
        {% else %}
            <p class="empty">Add transactions to generate charts.</p>
        {% endif %}
    </div>

    <div class="panel">
        <h3>Expense by Category</h3>
        {% if category_records %}
        <table>
            <tr><th>Category</th><th>Total Expenses</th></tr>
            {% for c in category_records %}
            <tr><td>{{ c.category_name }}</td>
            <td>₹{{ "%.2f"|format(c.total|float) }}</td></tr>
            {% endfor %}
        </table>
        {% else %}
        <p class="empty">No expense data available.</p>
        {% endif %}
    </div>
    """
    return page(
        content,
        income=income,
        expenses=expenses,
        savings=savings,
        chart=chart,
        category_records=category_records
    )


# -------------------- ERROR HANDLERS --------------------

@app.errorhandler(404)
def not_found(error):
    return page("""
        <h1>Page Not Found</h1>
        <p>The page you requested does not exist.</p>
        <a class="btn" href="/">Back to Dashboard</a>
    """), 404


if __name__ == "__main__":
    app.run(debug=True)
