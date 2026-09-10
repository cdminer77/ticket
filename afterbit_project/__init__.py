import pymysql
pymysql.install_as_MySQLdb()

# Bypass strict Django 6.1 MySQL version check for MySQL 8.0.x
from django.db.backends.base.base import BaseDatabaseWrapper
BaseDatabaseWrapper.check_database_version_supported = lambda self: None
