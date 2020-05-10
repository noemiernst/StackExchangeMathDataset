import sqlite3

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


def create_table(database, table_name, sql, if_exists='delete'):
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
    create_table(database, "AnswersMeta", 'CREATE TABLE "AnswersMeta" ( "AnswerId" INTEGER PRIMARY KEY, "QuestionId" INTEGER, "CreationDate" TEXT, "Score" INTEGER, "OwnerUserId" INTEGER )')
    create_table(database, "AnswersText", 'CREATE TABLE "AnswersText" ("AnswerId" INTEGER PRIMARY KEY, "Body" TEXT)')
    create_table(database, "Badges", 'CREATE TABLE "Badges" ( "UserId" INTEGER, "BadgeName" TEXT, "BadgeDate" TEXT, PRIMARY KEY(UserId, BadgeName, BadgeDate))')
    create_table(database, "Comments", 'CREATE TABLE "Comments" ("CommentId" INTEGER PRIMARY KEY, "PostId" INTEGER, "UserId" INTEGER, "Score" INTEGER, "Text" TEXT, "CreationDate" TEXT)')
    create_table(database, "DuplicateQuestions", 'CREATE TABLE "DuplicateQuestions" ( "QuestionId" INTEGER, "RelatedQuestionId" INTEGER, PRIMARY KEY(QuestionId, RelatedQuestionId) )')
    create_table(database, "FormulasComments", 'CREATE TABLE "FormulasComments"("FormulaId" INTEGER PRIMARY KEY, "CommentId" INTEGER, "Body" TEXT)')
    create_table(database, "FormulasPosts", 'CREATE TABLE "FormulasPosts"("FormulaId" INTEGER PRIMARY KEY, "PostId" INTEGER, "Body" TEXT)')
    create_table(database, "PostIdRelatedPostId", 'CREATE TABLE "PostIdRelatedPostId" ( "PostId" INTEGER, "RelatedPostId" INTEGER, "LinkTypeId" INTEGER, PRIMARY KEY(PostId, RelatedPostId, LinkTypeId))')
    create_table(database, "QuestionAcceptedAnswer", 'CREATE TABLE "QuestionAcceptedAnswer" ( "QuestionId" INTEGER PRIMARY KEY, "AcceptedAnswerId" INTEGER )')
    create_table(database, "QuestionTags", 'CREATE TABLE "QuestionTags" ( "QuestionId" INTEGER PRIMARY KEY, "Tags" TEXT )')
    create_table(database, "QuestionsMeta", 'CREATE TABLE "QuestionsMeta" ( "QuestionId" INTEGER PRIMARY KEY, "CreationDate" TEXT, "ViewCount" INTEGER, "Score" INTEGER, "OwnerUserId" INTEGER, "AnswerCount" INTEGER )')
    create_table(database, "QuestionsText", 'CREATE TABLE "QuestionsText" ( "QuestionId" INTEGER PRIMARY KEY, "Title" TEXT, "Body" TEXT )')
    create_table(database, "RelatedQuestionsSource2Target", 'CREATE TABLE "RelatedQuestionsSource2Target" ( "QuestionId" INTEGER, "RelatedQuestionId" INTEGER, PRIMARY KEY(QuestionId, RelatedQuestionId))')


#max_column_value("../output/mathematics.db", "FormulasComments", "FormulaId")
