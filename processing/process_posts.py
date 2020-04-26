try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import os.path
import pandas as pd
from processing.helper import write_table

def process_question_tags(questions, database):
    df = pd.DataFrame({"QuestionId": questions["QuestionId"], "Tags": questions["Tags"]})

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


def process_question_text(questions, database):
    df = pd.DataFrame({"QuestionId": questions["QuestionId"], "Title": questions["Title"], "Body": questions["Body"]})
    write_table(database, "QuestionsText", df)

def process_answer_body(answers, database):
    df = pd.DataFrame({"AnswerId": answers["AnswerId"], "Body": answers["Body"]})
    write_table(database, "AnswersText", df)

def process_common_attributes(posts, elem):
    # common attributes between questions and answers
    try:
        owneruserid = int(elem.attrib["OwnerUserId"])
    except Exception as e:
        # print index,e
        return False
    posts["CreationDate"].append(elem.attrib["CreationDate"])
    posts["Score"].append(int(elem.attrib["Score"]))
    posts["Body"].append(elem.attrib["Body"])
    # posts["CommentCount"].append(int(elem.attrib["CommentCount"]))
    posts["OwnerUserId"].append(owneruserid)
    # posts["LastEditorUserId"].append(int(elem.attrib["LastEditorUserId"]) if ("LastEditorUserId" in elem.attrib) else None)
    return True

def process_element(posts, elem, PostTypeId):
    index = int(elem.attrib["Id"])
    posttypeid = int(elem.attrib["PostTypeId"])

    if (PostTypeId == posttypeid) and (posttypeid == 1):
        # question
        if not process_common_attributes(posts, elem):
            return
        posts["QuestionId"].append(index)
        posts["ViewCount"].append(int(elem.attrib["ViewCount"]))
        posts["Title"].append(elem.attrib["Title"])
        posts["Tags"].append(elem.attrib["Tags"])
        posts["AnswerCount"].append(int(elem.attrib["AnswerCount"]))
        posts["AcceptedAnswerId"].append(
            int(elem.attrib["AcceptedAnswerId"]) if ("AcceptedAnswerId" in elem.attrib) else None)

    elif (PostTypeId == posttypeid) and (posttypeid == 2):
        # answer
        if not process_common_attributes(posts, elem):
            return
        posts["AnswerId"].append(index)
        posts["QuestionId"].append(int(elem.attrib["ParentId"]))

def init_posts(PostTypeId=1):
    posts = {}
    posts["CreationDate"] = []
    posts["Score"] = []
    posts["Body"] = []
    posts["CommentCount"] = []
    posts["OwnerUserId"] = []
    posts["LastEditorUserId"] = []
    if PostTypeId == 1:
        # question
        posts["QuestionId"] = []
        posts["ViewCount"] = []
        posts["Title"] = []
        posts["Tags"] = []
        posts["AnswerCount"] = []
        posts["AcceptedAnswerId"] = []
    else:
        # answer
        posts["AnswerId"] = []
        posts["QuestionId"] = []
    return posts

def posts_processing(directory, database):

    questions = init_posts(PostTypeId=1)
    answers = init_posts(PostTypeId=2)

    for event, elem in ET.iterparse(os.path.join(directory, "Posts.xml")):
        if event == "end":
            try:
                # print elem.tag,elem.attrib
                process_element(questions, elem, PostTypeId=1)
                process_element(answers, elem, PostTypeId=2)
                elem.clear()
            except Exception as e:
                pass
            # print("Exception: %s" % e)

    process_question_text(questions, database)
    process_answer_body(answers, database)
    process_question_tags(questions, database)

    return questions, answers
