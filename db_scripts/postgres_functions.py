import pandas as pd

def create_sql_tables_from_json(schema, extra_sql_args = ""):
    sql_query = "DROP TABLE IF EXISTS " + schema['schema'] + '.' + schema['table_name'] + "; "
    sql_query += "CREATE TABLE " + schema['schema'] + '.' + \
    schema['table_name'] + "("
    
    col_queries = []
    for column_name, column_properties in schema["fields"].items():
        col_query = column_name
        
        if column_name == schema['primary_key']:
            col_query += " SERIAL PRIMARY KEY"
            
        else:
            col_query +=  " " + column_properties["postgres_type"]
            if "default" in column_properties:
                col_query += " DEFAULT " + column_properties["default"]

            if column_properties["nullable"]:
                col_query +=  " NULL"
            else:
                col_query += " NOT NULL"
        
            if column_properties['unique']:
                col_query += " UNIQUE"
        
        col_queries.append(col_query)
        
    col_queries = ", ".join(col_queries)
    
    sql_query += col_queries
    sql_query += extra_sql_args
    sql_query += ");"

    return sql_query

def insert_row_query(row, table_name, schema):
    for column,value in row.items():
        if pd.isna(value):
            row[column] = "NULL"
        else:
            dtype = schema["fields"][column]["postgres_type"]
            if dtype == "TEXT" or dtype == "TIMESTAMP":
                row[column] = "'" + str(value) + "'"
            elif dtype == "INTEGER" or dtype == "FLOAT" or dtype == "BOOLEAN":
                row[column] = str(value)
    sql_query = "INSERT INTO " + table_name + " ("
    sql_query += ", ".join(row.keys()) + ") VALUES ("
    sql_query += ", ".join(row.values()) + ");"

    return sql_query