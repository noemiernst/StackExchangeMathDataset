try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import pandas as pd
import os.path
from helper import write_table

def comments_processing(directory, database):
    comments = {"CommentId": [],"PostId":[],"UserId":[],"Score":[],"Text":[],"CreationDate":[]}
    comment_index = 0
    for event,elem in ET.iterparse(os.path.join(directory, "Comments.xml")):
            if event == "end":
                try:
                    postid = int(elem.attrib["PostId"])
                    userid = int(elem.attrib["UserId"])
                    score = int(elem.attrib["Score"])
                    creationdate = elem.attrib["CreationDate"]
                    text = elem.attrib["Text"]

                    comments["CommentId"].append(comment_index)
                    comments["PostId"].append(postid)
                    comments["UserId"].append(userid)
                    comments["Score"].append(score)
                    comments["CreationDate"].append(creationdate)
                    comments["Text"].append(text)
                    elem.clear()

                    comment_index +=1
                except Exception as e:
                    pass
    assert len(comments["PostId"]) == len(comments["UserId"]) and len(comments["UserId"]) == len(comments["Score"]) and \
           len(comments["Score"]) == len(comments["CreationDate"]) and len(comments["Score"]) == len(comments["Text"])

    df = pd.DataFrame({"CommentId": comments["CommentId"], "PostId": comments["PostId"], "UserId": comments["UserId"],
                       "Score": comments["Score"], "Text": comments["Text"], "CreationDate": comments["CreationDate"]})
    write_table(database, 'Comments', df)
