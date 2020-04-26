try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import os.path
import pandas as pd
from processing.helper import write_table

def process_question_tags(output_dir, Questions, database):
    df = pd.DataFrame({"QuestionId": Questions["QuestionId"], "Tags": Questions["Tags"]})

    # rewrite this for database!!!
    '''
    tags_set = []
    question_tags = {}
    for q, t in zip(df["QuestionId"], df["Tags"]):
        tags = [tag[1:] for tag in t.split(">") if len(tag) > 0]
        tags_set += tags
        question_tags[q] = tags
    '''
    write_table(database, "QuestionTags", df)


def process_question_text(dir_path, Questions, database):
    df = pd.DataFrame({"QuestionId": Questions["QuestionId"], "Title": Questions["Title"], "Body": Questions["Body"]})
    write_table(database, "QuestionsText", df)

def process_answer_body(dir_path, Answers, database):
    df = pd.DataFrame({"AnswerId": Answers["AnswerId"], "Body": Answers["Body"]})
    write_table(database, "AnswersText", df)

def process_common_attributes(Posts, elem):
    # common attributes between questions and answers
    try:
        owneruserid = int(elem.attrib["OwnerUserId"])
    except Exception as e:
        # print index,e
        return False
    Posts["CreationDate"].append(elem.attrib["CreationDate"])
    Posts["Score"].append(int(elem.attrib["Score"]))
    Posts["Body"].append(elem.attrib["Body"])
    # Posts["CommentCount"].append(int(elem.attrib["CommentCount"]))
    Posts["OwnerUserId"].append(owneruserid)
    # Posts["LastEditorUserId"].append(int(elem.attrib["LastEditorUserId"]) if ("LastEditorUserId" in elem.attrib) else None)
    return True

def process_element(Posts, elem, PostTypeId):
    index = int(elem.attrib["Id"])
    posttypeid = int(elem.attrib["PostTypeId"])

    if (PostTypeId == posttypeid) and (posttypeid == 1):
        # question
        if not process_common_attributes(Posts, elem):
            return
        Posts["QuestionId"].append(index)
        Posts["ViewCount"].append(int(elem.attrib["ViewCount"]))
        Posts["Title"].append(elem.attrib["Title"])
        Posts["Tags"].append(elem.attrib["Tags"])
        Posts["AnswerCount"].append(int(elem.attrib["AnswerCount"]))
        Posts["AcceptedAnswerId"].append(
            int(elem.attrib["AcceptedAnswerId"]) if ("AcceptedAnswerId" in elem.attrib) else None)

    elif (PostTypeId == posttypeid) and (posttypeid == 2):
        # answer
        if not process_common_attributes(Posts, elem):
            return
        Posts["AnswerId"].append(index)
        Posts["QuestionId"].append(int(elem.attrib["ParentId"]))

def init_posts(PostTypeId=1):
    Posts = {}
    Posts["CreationDate"] = []
    Posts["Score"] = []
    Posts["Body"] = []
    Posts["CommentCount"] = []
    Posts["OwnerUserId"] = []
    Posts["LastEditorUserId"] = []
    if PostTypeId == 1:
        # question
        Posts["QuestionId"] = []
        Posts["ViewCount"] = []
        Posts["Title"] = []
        Posts["Tags"] = []
        Posts["AnswerCount"] = []
        Posts["AcceptedAnswerId"] = []
    else:
        # answer
        Posts["AnswerId"] = []
        Posts["QuestionId"] = []
    return Posts

def posts_processing(directory, database):

    Questions = init_posts(PostTypeId=1)
    Answers = init_posts(PostTypeId=2)

    for event, elem in ET.iterparse(os.path.join(directory, "Posts.xml")):
        if event == "end":
            try:
                # print elem.tag,elem.attrib
                process_element(Questions, elem, PostTypeId=1)
                process_element(Answers, elem, PostTypeId=2)
                elem.clear()
            except Exception as e:
                pass
            # print("Exception: %s" % e)

    process_question_text(directory, Questions, database)
    process_answer_body(directory, Answers, database)
    process_question_tags(directory, Questions, database)
