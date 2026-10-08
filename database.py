import os
import mysql.connector
from mysql.connector import pooling


dbconfig = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "autocommit": True
}


connection_pool = pooling.MySQLConnectionPool(
    pool_name="online_products_pool",
    pool_size=5,
    pool_reset_session=True,
    **dbconfig
)


def get_connection():
    return connection_pool.get_connection()