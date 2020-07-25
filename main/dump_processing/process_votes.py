try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import os.path
import pandas as pd
from helper import log
from helper import write_table
import sqlite3
from pathlib import Path

def bounty_processing(directory, database):
    d = {"PostId":[],"BountyAmount":[]}
    for event,elem in ET.iterparse(os.path.join(directory, "Votes.xml")):
            if event == "end":
                try:
                    if "BountyAmount" in elem.attrib:
                        postid = int(elem.attrib["PostId"])
                        bounty = int(elem.attrib["BountyAmount"])
                        d["PostId"].append(postid)
                        d["BountyAmount"].append(bounty)
                    elem.clear()
                except Exception as e:
                    pass

    DB = sqlite3.connect(database)
    answers_meta = pd.read_sql('select AnswerId, QuestionId from "AnswersMeta"', DB)
    DB.close()

    question_bounty = {"QuestionId":[],"Bounty":[]}
    for postid,bounty in zip(d["PostId"],d["BountyAmount"]):
        if answers_meta[answers_meta["QuestionId"] == postid].index.tolist():
            question_bounty["QuestionId"].append(postid)
            question_bounty["Bounty"].append(bounty)

    df = pd.DataFrame(question_bounty)
    write_table(database, "Question_Bounty", df)
    statistics_file = os.path.join(Path(database).parent, "statistics.log")
    log(statistics_file, "# questions having bounty: " + str(len(df)))
