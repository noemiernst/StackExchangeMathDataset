try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import os.path
import pandas as pd
import argparse
import sqlite3
from helper import write_table
from helper import log

def badge_processing(directory, database):
    index = []
    UserId = []
    BadgeName = []
    BadgeDate = []

    for event,elem in ET.iterparse(os.path.join(directory, "Badges.xml")):
        if event == "end":
            try:
                ind = int(elem.attrib["Id"])
                userid = int(elem.attrib["UserId"])
                badgename = elem.attrib["Name"]
                badgedate = elem.attrib["Date"]
                index.append(ind)
                UserId.append(userid)
                BadgeName.append(badgename)
                BadgeDate.append(badgedate)
                elem.clear()
            except Exception as e:
                pass

    df =pd.DataFrame({"UserId":UserId,"BadgeName":BadgeName,"BadgeDate":BadgeDate})
    write_table(database, "Badges", df)
    log("../output/statistics.log","# users having badges: %d" % len(df))
