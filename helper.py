import sqlite3

def write_table(database, table_name, dataframe, if_exists='append', index=False):
    DB = sqlite3.connect(database)
    dataframe.to_sql(name=table_name, con=DB, if_exists=if_exists, index=index)
    DB.close()
    print("wrote ", len(dataframe), " entries in table ", table_name, " of database ", database)

def execute_sql(database, sql):
    DB = sqlite3.connect(database)
    cursor = DB.cursor()
    cursor.execute(sql)
    DB.commit()
    DB.close()

def log(file,line):
    print(line)
    with open(file,"a") as f:
        f.write("%s \n" % line)
