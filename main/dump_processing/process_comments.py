try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import pandas as pd
import os.path
from dump_processing.helper import write_table
from dump_processing.helper import log
from pathlib import Path

def comments_processing(site_name, directory, database):
    comments = {"Site": [], "CommentId": [],"PostId":[],"UserId":[],"Score":[],"Text":[],"CreationDate":[]}
    comment_index = 0

    comments_dict = {}

    for event,elem in ET.iterparse(os.path.join(directory, "Comments.xml")):
        if event == "end":
            try:
                postid = int(elem.attrib["PostId"])
                userid = int(elem.attrib["UserId"])
                score = int(elem.attrib["Score"])
                creationdate = elem.attrib["CreationDate"]
                text = elem.attrib["Text"]

                comments["Site"].append(site_name)
                comments["CommentId"].append(comment_index)
                comments["PostId"].append(postid)
                comments["UserId"].append(userid)
                comments["Score"].append(score)
                comments["CreationDate"].append(creationdate)
                comments["Text"].append(text)
                elem.clear()

                #comments_dict[comment_index] = text

                comment_index +=1
            except Exception as e:
                pass
        if(len(comments["CommentId"])>1000000):
            df = pd.DataFrame({"Site": comments["Site"],"CommentId": comments["CommentId"], "PostId": comments["PostId"], "UserId": comments["UserId"],
                       "Score": comments["Score"], "Text": comments["Text"], "CreationDate": comments["CreationDate"]})
            write_table(database, 'Comments', df)
            comments = {"Site": [], "CommentId": [],"PostId":[],"UserId":[],"Score":[],"Text":[],"CreationDate":[]}

    df = pd.DataFrame({"Site": comments["Site"],"CommentId": comments["CommentId"], "PostId": comments["PostId"], "UserId": comments["UserId"],
               "Score": comments["Score"], "Text": comments["Text"], "CreationDate": comments["CreationDate"]})
    write_table(database, 'Comments', df)
    statistics_file = os.path.join(Path(database).parent, "statistics.log")
    log(statistics_file, "# comments: " + str(len(df)))
