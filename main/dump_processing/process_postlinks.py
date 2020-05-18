try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import os.path
import pandas as pd
from dump_processing.helper import write_table
from dump_processing.helper import log


def duplicate_questions(database, df):
    result = df.groupby("LinkTypeId")
    for k, v in result:
        d = pd.DataFrame({"QuestionId": v["PostId"], "RelatedQuestionId": v["RelatedPostId"]})
        if k == 3:
            log("../output/statistics.log", "# duplicate questions: %d" % len(d))
            file_name = "DuplicateQuestions"
        if k == 1:
            log("../output/statistics.log", "# related questions: %d" % len(d))
            file_name = "RelatedQuestionsSource2Target"
        write_table(database, file_name, d)


def postlinks_processing(directory, database):
    d = {"PostId": [], "RelatedPostId": [], "LinkTypeId": []}
    for event, elem in ET.iterparse(os.path.join(directory, "PostLinks.xml")):
        if event == "end":
            try:
                postid = int(elem.attrib["PostId"])
                relatedpostid = int(elem.attrib["RelatedPostId"])
                linktypeid = int(elem.attrib["LinkTypeId"])
                d["PostId"].append(postid)
                d["RelatedPostId"].append(relatedpostid)
                d["LinkTypeId"].append(linktypeid)
                elem.clear()
            except Exception as e:
                pass

    df = pd.DataFrame(d)
    write_table(database, "PostIdRelatedPostId", df)
    #duplicate_questions(database, df)
