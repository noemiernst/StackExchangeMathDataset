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
    for event, elem in ET.iterparse(os.path.join(directory, "Users.xml")):
        if event == "end":
            try:
                userid = int(elem.attrib["AccountId"])
                reputation = int(elem.attrib["Reputation"])
                if userid not in d["UserId"]:
                    d["Site"].append(site_name)
                    d["UserId"].append(userid)
                    d["Reputation"].append(reputation)
                elem.clear()
            except Exception as e:
                pass

    df = pd.DataFrame(d)
    print([item for item, count in collections.Counter(d["UserId"]).items() if count > 1])
    write_table(database, "Users", df)
