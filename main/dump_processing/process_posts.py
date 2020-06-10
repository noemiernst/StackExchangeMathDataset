try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
try:
    import cPickle as pickle
except ImportError:
    import pickle
import os.path
import pandas as pd
from dump_processing.helper import write_table
from dump_processing.helper import log

def process_answer_meta(site_name, answers, database):
    sites = [site_name for i in range(len(answers["AnswerId"]))]
    df = pd.DataFrame({"Site": sites, "AnswerId": answers["AnswerId"],"QuestionId": answers["QuestionId"], "CreationDate": answers["CreationDate"],
                       "Score": answers["Score"],
                       #"CommentCount": answers["CommentCount"],
                       #"LastEditorUserId": answers["LastEditorUserId"],
                       "OwnerUserId": answers["OwnerUserId"]})
    write_table(database, "AnswerMeta", df)

def process_question_meta(site_name, questions, database):
    sites = [site_name for i in range(len(questions["QuestionId"]))]
    df = pd.DataFrame({"Site": sites, "QuestionId": questions["QuestionId"], "CreationDate": questions["CreationDate"],
                       "ViewCount": questions["ViewCount"], "Score": questions["Score"],
                       #"CommentCount": questions["CommentCount"],
                       "OwnerUserId": questions["OwnerUserId"],
                       #"LastEditorUserId": questions["LastEditorUserId"],
                       "AnswerCount": questions["AnswerCount"]})
    write_table(database, "QuestionMeta", df)

def process_question_acceptedanswer(site_name, questions, database):
    sites = []
    questionId = []
    acceptedAnswerId = []
    for qid, aid in zip(questions["QuestionId"], questions["AcceptedAnswerId"]):
        if aid:
            sites.append(site_name)
            questionId.append(qid)
            acceptedAnswerId.append(aid)
    df = pd.DataFrame({"Site": sites, "QuestionId": questionId, "AcceptedAnswerId": acceptedAnswerId})

    write_table(database, "QuestionAcceptedAnswer", df)
    log("../output/statistics.log", "# question-acceptedAnswer pairs: %d" % len(df))


def process_question_tags(site_name, questions, database):
    sites = [site_name for i in range(len(questions["QuestionId"]))]
    df = pd.DataFrame({"Site": sites, "QuestionId": questions["QuestionId"], "Tags": questions["Tags"]})
    write_table(database, "QuestionTags", df)
    questions.pop("Tags")
    '''
    tags_set = []
    question_tags = {}
    question_tag = {}
    question_tag["QuestionId"]= []
    question_tag["Tag"]= []
    for q, t in zip(df["QuestionId"], df["Tags"]):
        tags = [tag[1:] for tag in t.split(">") if len(tag) > 0]
        tags_set += tags
        question_tags[q] = tags
        for tag in tags:
            question_tag["QuestionId"].append(q)
            question_tag["Tag"].append(tag)
    df = pd.DataFrame({"QuestionId": question_tag["QuestionId"], "Tag": question_tag["Tag"]})
    write_table(database, "QuestionTag", df)

    log("../output/statistics.log", "# questions with tags: " + str(len(question_tags)))
    log("../output/statistics.log", "# unique tags: " + str(len(set(tags_set))))'''

def process_question_text(site_name, questions, database, directory):
    sites = [site_name for i in range(len(questions["QuestionId"]))]
    df = pd.DataFrame({"Site": sites, "QuestionId": questions["QuestionId"], "Title": questions["Title"], "Body": questions["Body"]})
    write_table(database, "QuestionText", df)

    #questions_dict = {}
    #for question,title,body in zip(questions["QuestionId"],questions["Title"],questions["Body"]):
    #    questions_dict[question] = [title,body]
    #with open(os.path.join(directory, "questiontext.pkl"),"wb") as f:
    #    pickle.dump(questions_dict,f)
    questions.pop("Title")
    questions.pop("Body")

def process_answer_body(site_name, answers, database, directory):
    sites = [site_name for i in range(len(answers["AnswerId"]))]
    df = pd.DataFrame({"Site": sites, "AnswerId": answers["AnswerId"], "Body": answers["Body"]})
    write_table(database, "AnswerText", df)

    #answers_dict = {}
    #for question,body in zip(answers["AnswerId"],answers["Body"]):
    #    answers_dict[question] = body
    #with open(os.path.join(directory, "answertext.pkl"),"wb") as f:
    #    pickle.dump(answers_dict,f)

    answers.pop("Body")

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

def posts_processing(site_name, directory, database):

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

    log("../output/statistics.log", "# posts: " + str(len(questions["QuestionId"])+len(answers["AnswerId"])))
    log("../output/statistics.log", "# questions: " + str(len(questions["QuestionId"])))
    log("../output/statistics.log", "# answers: " + str(len(answers["AnswerId"])))

    process_question_text(site_name, questions, database, directory)
    process_question_tags(site_name, questions, database)
    process_question_acceptedanswer(site_name, questions, database)
    process_question_meta(site_name, questions, database)
    questions.clear()  # 'clear questions dictionary to free up memory space
    process_answer_body(site_name, answers, database, directory)
    process_answer_meta(site_name, answers, database)
