import sqlite3

def write_table(database, table_name, dataframe, if_exists='replace', index=False):
    DB = sqlite3.connect(database)
    dataframe.to_sql(name=table_name, con=DB, if_exists=if_exists, index=index)
    DB.close()
    print("# wrote table ", table_name, " to database ", database, " with ", len(dataframe), " entries")
