try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import pandas as pd
import os.path
from processing.helper import write_table

def comments_processing(directory, database):
    d = {"CommentId": [],"PostId":[],"UserId":[],"Score":[],"Text":[],"CreationDate":[]}
    comment_index = 0
    for event,elem in ET.iterparse(os.path.join(directory, "Comments.xml")):
            if event == "end":
                try:
                    postid = int(elem.attrib["PostId"])
                    userid = int(elem.attrib["UserId"])
                    score = int(elem.attrib["Score"])
                    creationdate = elem.attrib["CreationDate"]
                    text = elem.attrib["Text"]

                    d["CommentId"].append(comment_index)
                    d["PostId"].append(postid)
                    d["UserId"].append(userid)
                    d["Score"].append(score)
                    d["CreationDate"].append(creationdate)
                    d["Text"].append(text)
                    elem.clear()

                    comment_index +=1
                except Exception as e:
                    pass
    assert len(d["PostId"]) == len(d["UserId"]) and len(d["UserId"]) == len(d["Score"]) and \
           len(d["Score"]) == len(d["CreationDate"]) and len(d["Score"]) == len(d["Text"])

    df = pd.DataFrame({"CommentId": d["CommentId"], "PostId": d["PostId"], "UserId": d["UserId"],
                       "Score": d["Score"], "Text": d["Text"], "CreationDate": d["CreationDate"]})
    write_table(database, 'Comments', df)

    return d
