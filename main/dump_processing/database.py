import sqlite3
from dump_processing.helper import log

def max_column_value(database, table_name, column_name):
    DB = sqlite3.connect(database)
    cursor = DB.cursor()

    value = cursor.execute("SELECT MAX(" + column_name+ ") AS LargestValue FROM " + table_name + ";")
    max = value.fetchone()[0]
    if max == None:
        max = 0
    DB.commit()
    DB.close()
    return max


def create_table(database, table_name, sql, if_exists='nothing'):
    DB = sqlite3.connect(database)
    cursor = DB.cursor()

    cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='"+ table_name +"' ")

    #if the count is 1, then table exists
    if cursor.fetchone()[0]==1 :
        if if_exists == 'delete':
            cursor.execute("DROP TABLE " + table_name)
            cursor.execute(sql)
    else:
        cursor.execute(sql)

    DB.commit()
    DB.close()

def create_tables(database):
    create_table(database, "SiteFileHash", 'CREATE TABLE "SiteFileHash" ("Site" TEXT PRIMARY KEY, "MD5Hash" TEXT)')
    create_table(database, "AnswerMeta", 'CREATE TABLE "AnswerMeta" ("Site" TEXT, "AnswerId" INTEGER, "QuestionId" INTEGER, "CreationDate" TEXT, "Score" INTEGER, "OwnerUserId" INTEGER, PRIMARY KEY(Site, AnswerId))')
    create_table(database, "AnswerText", 'CREATE TABLE "AnswerText" ("Site" TEXT, "AnswerId" INTEGER, "Body" TEXT, PRIMARY KEY(Site, AnswerId))')
    create_table(database, "Badges", 'CREATE TABLE "Badges" ("Site" TEXT, "BadgeId" INTEGER,"UserId" INTEGER, "BadgeName" TEXT, "BadgeDate" TEXT, PRIMARY KEY(Site, BadgeId))')
    create_table(database, "Comments", 'CREATE TABLE "Comments" ("Site" TEXT, "CommentId" INTEGER, "PostId" INTEGER, "UserId" INTEGER, "Score" INTEGER, "Text" TEXT, "CreationDate" TEXT, PRIMARY KEY(Site, CommentId))')
    #create_table(database, "DuplicateQuestions", 'CREATE TABLE "DuplicateQuestions" ( "QuestionId" INTEGER, "RelatedQuestionId" INTEGER, PRIMARY KEY(QuestionId, RelatedQuestionId) )')
    create_table(database, "FormulasComments", 'CREATE TABLE "FormulasComments"("FormulaId" INTEGER PRIMARY KEY, "Site" TEXT, "CommentId" INTEGER, "Body" TEXT, "TokenLength" INTEGER, "StartingPosition" INTEGER)')
    create_table(database, "FormulasPosts", 'CREATE TABLE "FormulasPosts"("FormulaId" INTEGER PRIMARY KEY, "Site" TEXT, "PostId" INTEGER, "Body" TEXT, "TokenLength" INTEGER, "StartingPosition" INTEGER)')
    create_table(database, "PostIdRelatedPostId", 'CREATE TABLE "PostIdRelatedPostId" ("Site" TEXT, "PostId" INTEGER, "RelatedPostId" INTEGER, "LinkTypeId" INTEGER, PRIMARY KEY(Site, PostId, RelatedPostId, LinkTypeId))')
    create_table(database, "QuestionAcceptedAnswer", 'CREATE TABLE "QuestionAcceptedAnswer" ("Site" TEXT, "QuestionId" INTEGER, "AcceptedAnswerId" INTEGER, PRIMARY KEY(Site, QuestionId))')
    create_table(database, "QuestionTags", 'CREATE TABLE "QuestionTags" ("Site" TEXT, "QuestionId" INTEGER, "Tags" TEXT, PRIMARY KEY(Site, QuestionId) )')
    create_table(database, "QuestionMeta", 'CREATE TABLE "QuestionMeta" ("Site" TEXT, "QuestionId" INTEGER, "CreationDate" TEXT, "ViewCount" INTEGER, "Score" INTEGER, "OwnerUserId" INTEGER, "AnswerCount" INTEGER, PRIMARY KEY(Site, QuestionId))')
    create_table(database, "QuestionText", 'CREATE TABLE "QuestionText" ("Site" TEXT, "QuestionId" INTEGER, "Title" TEXT, "Body" TEXT,  PRIMARY KEY(Site, QuestionId) )')
    #create_table(database, "RelatedQuestionsSource2Target", 'CREATE TABLE "RelatedQuestionsSource2Target" ( "QuestionId" INTEGER, "RelatedQuestionId" INTEGER, PRIMARY KEY(QuestionId, RelatedQuestionId))')
    create_table(database, "FormulaContext", 'CREATE TABLE "FormulaContext" ("FormulaId" INTEGER PRIMARY KEY, "Context" STRING)')

def remove_site(site, database):
    log("../output/statistics.log", "Removing old database entries of site " + site)

    tables = ["AnswerMeta", "AnswerText", "Badges", "Comments", "FormulasComments", "FormulasPosts", "PostIdRelatedPostId",
              "QuestionAcceptedAnswer", "QuestionTags", "QuestionText"]
    DB = sqlite3.connect(database)
    cursor = DB.cursor()

    for table in tables:
        cursor.execute("DELETE FROM '"+ table + "' WHERE site = '" + site + "'")

    #TODO: delete formula context of formulas that were deleted

    DB.commit()
    DB.close()

