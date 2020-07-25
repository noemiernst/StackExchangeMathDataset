import sqlite3
from dump_processing.helper import log
import os
from pathlib import Path

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
    create_table(database, "Badges", 'CREATE TABLE "Badges" ("Site" TEXT, "BadgeId" INTEGER,"UserId" INTEGER, "BadgeName" TEXT, "BadgeClass" TEXT, "BadgeDate" TEXT, PRIMARY KEY(Site, BadgeId))')
    create_table(database, "Comments", 'CREATE TABLE "Comments" ("Site" TEXT, "CommentId" INTEGER, "PostId" INTEGER, "UserId" INTEGER, "Score" INTEGER, "Text" TEXT, "CreationDate" TEXT, PRIMARY KEY(Site, CommentId))')
    #create_table(database, "DuplicateQuestions", 'CREATE TABLE "DuplicateQuestions" ( "QuestionId" INTEGER, "RelatedQuestionId" INTEGER, PRIMARY KEY(QuestionId, RelatedQuestionId) )')
    create_table(database, "FormulasComments", 'CREATE TABLE "FormulasComments"("FormulaId" INTEGER PRIMARY KEY, "Site" TEXT, "CommentId" INTEGER, "LaTeXBody" TEXT, "TokenLength" INTEGER, "StartingPosition" INTEGER, "Inline" BOOLEAN)')
    create_table(database, "FormulasPosts", 'CREATE TABLE "FormulasPosts"("FormulaId" INTEGER PRIMARY KEY, "Site" TEXT, "PostId" INTEGER, "LaTeXBody" TEXT, "TokenLength" INTEGER, "StartingPosition" INTEGER, "Inline" BOOLEAN)')
    create_table(database, "PostIdRelatedPostId", 'CREATE TABLE "PostIdRelatedPostId" ("Site" TEXT, "PostId" INTEGER, "RelatedPostId" INTEGER, "LinkTypeId" INTEGER, PRIMARY KEY(Site, PostId, RelatedPostId, LinkTypeId))')
    create_table(database, "QuestionAcceptedAnswer", 'CREATE TABLE "QuestionAcceptedAnswer" ("Site" TEXT, "QuestionId" INTEGER, "AcceptedAnswerId" INTEGER, PRIMARY KEY(Site, QuestionId))')
    create_table(database, "QuestionTags", 'CREATE TABLE "QuestionTags" ("Site" TEXT, "QuestionId" INTEGER, "Tags" TEXT, PRIMARY KEY(Site, QuestionId) )')
    create_table(database, "QuestionMeta", 'CREATE TABLE "QuestionMeta" ("Site" TEXT, "QuestionId" INTEGER, "CreationDate" TEXT, "ViewCount" INTEGER, "Score" INTEGER, "OwnerUserId" INTEGER, "AnswerCount" INTEGER, PRIMARY KEY(Site, QuestionId))')
    create_table(database, "QuestionText", 'CREATE TABLE "QuestionText" ("Site" TEXT, "QuestionId" INTEGER, "Title" TEXT, "Body" TEXT,  PRIMARY KEY(Site, QuestionId) )')
    #create_table(database, "RelatedQuestionsSource2Target", 'CREATE TABLE "RelatedQuestionsSource2Target" ( "QuestionId" INTEGER, "RelatedQuestionId" INTEGER, PRIMARY KEY(QuestionId, RelatedQuestionId))')
    create_table(database, "FormulaContext", 'CREATE TABLE "FormulaContext" ("FormulaId" INTEGER PRIMARY KEY, "Context" STRING)')
    create_table(database, "Users", 'CREATE TABLE "Users" ("Site" TEXT, "UserId" INTEGER, "Reputation" INTEGER, PRIMARY KEY(Site, UserId))')
    create_table(database, "Tags", 'CREATE TABLE "Tags" ("Site" TEXT, "Tag" TEXT, "Count" INTEGER, PRIMARY KEY(Site, Tag))')

def remove_site(site, database):
    statistics_file = os.path.join(Path(database).parent, "statistics.log")
    log(statistics_file, "Removing old database entries of site " + site)

    tables = ["AnswerMeta", "AnswerText", "Badges", "Comments", "FormulasComments", "FormulasPosts", "PostIdRelatedPostId",
              "QuestionAcceptedAnswer", "QuestionTags", "QuestionText", "QuestionMeta", "Users", "Tags"]
    DB = sqlite3.connect(database)
    cursor = DB.cursor()

    for table in tables:
        cursor.execute("DELETE FROM '"+ table + "' WHERE site = '" + site + "'")

    tables = ["FormulasPostsMathML", "FormulasCommentsMathML"]

    for table in tables:
        cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='"+ table +"' ")
        #if the count is 1, then table exists
        if cursor.fetchone()[0]==1 :
            cursor.execute("DELETE FROM '"+ table + "' WHERE site = '" + site + "'")

    DB.commit()
    DB.close()

