try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import os.path
import pandas as pd
from dump_processing.helper import write_table

def tags_processing(site_name, directory, database):
    d = {"Site": [], "Tag": [], "Count": []}
    for event, elem in ET.iterparse(os.path.join(directory, "Tags.xml")):
        if event == "end":
            try:
                tag = elem.attrib["TagName"]
                count = int(elem.attrib["Count"])
                d["Site"].append(site_name)
                d["Tag"].append(tag)
                d["Count"].append(count)
                elem.clear()
            except Exception as e:
                pass

    df = pd.DataFrame(d)
    write_table(database, "Tags", df)
