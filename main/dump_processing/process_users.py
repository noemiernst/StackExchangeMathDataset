try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import os.path
import pandas as pd
from dump_processing.helper import write_table
import collections

def users_processing(site_name, directory, database):
    d = {"Site": [], "UserId": [], "Reputation": []}
    user_set = set()
    for event, elem in ET.iterparse(os.path.join(directory, "Users.xml")):
        if event == "end":
            try:
                userid = int(elem.attrib["AccountId"])
                reputation = int(elem.attrib["Reputation"])
                if userid not in user_set:
                    d["Site"].append(site_name)
                    user_set.add(userid)
                    d["UserId"].append(userid)
                    d["Reputation"].append(reputation)
                elem.clear()
            except Exception as e:
                pass

    df = pd.DataFrame(d)
    write_table(database, "Users", df)
