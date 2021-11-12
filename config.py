DEBUG = "0"
# Dev PostGres Credentials
pg_user_dev = 'postgres'
pg_pass_dev = 'admin'
pg_db_dev = 'postgres'
pg_host_dev = 'localhost'
pg_port_dev = 5432

DEV_DB = f"postgresql://{pg_user_dev}:{pg_pass_dev}@{pg_host_dev}:{pg_port_dev}/{pg_db_dev}"

# Prod PostGres Credentials
pg_user_prod = ''
pg_pass_prod = ''
pg_db_prod = ''
pg_host_prod = ''
pg_port_prod = ''

PROD_DB = f"postgresql://{pg_user_prod}:{pg_pass_prod}@{pg_host_prod}:{pg_port_prod}/{pg_db_prod}"

APCA_API_KEY_ID = "PKEWNVWYFA4K6UCE92KK"
APCA_API_SECRET_KEY = "3yqxER2ddzIF3XLo3JKjJcAvyVlsemYuHK6N5cRo"
FLASK_SECRET_KEY = '546cfaac2bd3703f257f7a95'