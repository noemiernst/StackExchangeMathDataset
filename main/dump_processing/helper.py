import sqlite3
import sys

def write_table(database, table_name, dataframe, if_exists='append', index=False):
    DB = sqlite3.connect(database)
    dataframe.to_sql(name=table_name, con=DB, if_exists=if_exists, index=index)
    DB.close()
    print("wrote ", len(dataframe), " entries in table ", table_name, " of database ", database)

def update_table(database, table_name, dataframe, key):
    columns = list(dataframe.keys())
    #columns.remove(key)
    DB = sqlite3.connect(database)
    cursor = DB.cursor()
    for index, row in dataframe.iterrows():
        cursor.execute("SELECT "+ key + " FROM " + table_name + " where " + key + " = '" + str(row[key]) + "' LIMIT 1")
        if cursor.fetchone():
            attributes = []
            for col in columns:
                if columns.index(col) != 0:
                    attributes.append(", ")
                attributes.append(str(col) + "='" + str(row[col]) + "'")
            sql = "UPDATE "+ table_name +" SET "
            for a in attributes:
                sql += a + " "
            sql += "WHERE " + str(key) + "='" + str(row[key]) + "';"
            cursor.execute(sql)
        else:
            sql = "INSERT INTO " + table_name + " ("
            for col in columns:
                if columns.index(col) != 0:
                    sql += ", "
                sql += col
            sql += ") VALUES ("
            for col in columns:
                if columns.index(col) != 0:
                    sql += ", "
                sql += "'" + str(row[col]) + "'"
            sql += ");"
            cursor.execute(sql)
    DB.commit()
    DB.close()

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

def progress_bar(current, total, string, barLength = 20):
    percent = float(current) * 100 / total
    arrow   = '-' * int(percent/100 * barLength - 1) + '>'
    spaces  = ' ' * (barLength - len(arrow))

    sys.stdout.write('\rProgress: [%s%s] %d %%   %d/%d %s' % (arrow, spaces, percent, current, total, string))
    sys.stdout.flush()
