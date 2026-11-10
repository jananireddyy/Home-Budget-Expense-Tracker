# 💰 Home Budget – Expense Tracker and Analysis System

A web-based personal finance management application built using **Python, Flask, MySQL, HTML, CSS, and JavaScript**. It helps users manage their income, track expenses, set monthly budgets, and analyze their financial activities through visual reports.

## 📌 Project Overview

Managing personal finances can be difficult without proper tracking. This project provides a simple and user-friendly platform to record daily transactions, monitor spending, manage budgets, and understand financial habits.

## ✨ Features

- 📊 **Dashboard:** View total income, expenses, and net savings.
- 💳 **Transaction Management:** Add, view, edit, and delete transactions.
- 🏷️ **Category Management:** Organize income and expenses by category.
- 🎯 **Monthly Budget:** Set spending limits and monitor budget usage.
- 📈 **Reports & Analysis:** Analyze monthly income and expenses using charts.
- 📉 **Expense Analysis:** View spending by category.
- 🗄️ **Database Integration:** Store financial records using MySQL.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web application framework |
| MySQL | Database management |
| HTML5 | Web page structure |
| CSS3 | Styling and layout |
| JavaScript | Interactive features |
| Pandas | Data analysis |
| NumPy | Numerical calculations |
| Matplotlib | Data visualization |

## 📂 Project Structure

```text
Home_Budget/
│
├── app.py
├── config.py
├── database.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── database/
│   └── schema.sql
│
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── transactions.html
│   ├── transaction_form.html
│   ├── budgets.html
│   └── reports.html
│
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── script.js
```

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/jananireddyy/Home-Budget-Expense-Tracker.git
```

### 2. Navigate to the Project Folder

```bash
cd Home-Budget-Expense-Tracker
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure MySQL Database

- Install and start MySQL Server.
- Create a database named `home_budget`.
- Execute the SQL statements in `database/schema.sql` if setting up a fresh database.
- Configure your MySQL connection details in `config.py`.

**Note:** The database schema should be created before running the application. Do not overwrite an existing database containing important data.

### 6. Set the MySQL Password

In PowerShell:

```powershell
$securePassword = Read-Host "Enter MySQL password" -AsSecureString
$env:MYSQL_PASSWORD = [System.Net.NetworkCredential]::new("", $securePassword).Password
```

### 7. Run the Application

```bash
python app.py
```

### 8. Open in Browser

```text
http://127.0.0.1:5000
```

## 📸 Application Modules

The application includes five main modules:

1. Dashboard
2. Transactions
3. Add Transaction
4. Monthly Budgets
5. Reports & Analysis

## 🎯 Project Objectives

- Develop a simple personal finance management system.
- Track income and expenses efficiently.
- Help users control unnecessary spending.
- Monitor monthly budgets.
- Generate meaningful financial reports.
- Apply Python programming and database management concepts in a real-world application.

## 🔮 Future Enhancements

- User registration and login authentication.
- Interactive financial analytics.
- Export reports to PDF and Excel.
- Expense prediction and recommendations.
- Cloud deployment and online accessibility.

## 👨‍💻 Author

**Yaswanth Marpu**

GitHub: [@jananireddyy](https://github.com/jananireddyy)

## 📜 License

This project is available for educational and learning purposes. See the repository license for applicable reuse terms.

---

⭐ If you find this project useful, consider giving the repository a star!