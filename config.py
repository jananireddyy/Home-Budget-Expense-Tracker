import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "home-budget-development-key")
    MYSQL_HOST = "localhost"
    MYSQL_USER = "root"
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = "home_budget"
    MYSQL_PORT = 3306
