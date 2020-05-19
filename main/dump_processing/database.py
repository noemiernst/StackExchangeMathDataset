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
    create_table(database, "AnswersMeta", 'CREATE TABLE "AnswersMeta" ("Site" TEXT, "AnswerId" INTEGER, "QuestionId" INTEGER, "CreationDate" TEXT, "Score" INTEGER, "OwnerUserId" INTEGER, PRIMARY KEY(Site, AnswerId))')
    create_table(database, "AnswersText", 'CREATE TABLE "AnswersText" ("Site" TEXT, "AnswerId" INTEGER, "Body" TEXT, PRIMARY KEY(Site, AnswerId))')
    create_table(database, "Badges", 'CREATE TABLE "Badges" ("Site" TEXT, "BadgeId" INTEGER,"UserId" INTEGER, "BadgeName" TEXT, "BadgeDate" TEXT, PRIMARY KEY(Site, BadgeId))')
    create_table(database, "Comments", 'CREATE TABLE "Comments" ("Site" TEXT, "CommentId" INTEGER, "PostId" INTEGER, "UserId" INTEGER, "Score" INTEGER, "Text" TEXT, "CreationDate" TEXT, PRIMARY KEY(Site, CommentId))')
    #create_table(database, "DuplicateQuestions", 'CREATE TABLE "DuplicateQuestions" ( "QuestionId" INTEGER, "RelatedQuestionId" INTEGER, PRIMARY KEY(QuestionId, RelatedQuestionId) )')
    create_table(database, "FormulasComments", 'CREATE TABLE "FormulasComments"("FormulaId" INTEGER PRIMARY KEY, "Site" TEXT, "CommentId" INTEGER, "Body" TEXT, "TokenLength" INTEGER)')
    create_table(database, "FormulasPosts", 'CREATE TABLE "FormulasPosts"("FormulaId" INTEGER PRIMARY KEY, "Site" TEXT, "PostId" INTEGER, "Body" TEXT, "TokenLength" INTEGER)')
    create_table(database, "PostIdRelatedPostId", 'CREATE TABLE "PostIdRelatedPostId" ("Site" TEXT, "PostId" INTEGER, "RelatedPostId" INTEGER, "LinkTypeId" INTEGER, PRIMARY KEY(Site, PostId, RelatedPostId, LinkTypeId))')
    create_table(database, "QuestionAcceptedAnswer", 'CREATE TABLE "QuestionAcceptedAnswer" ("Site" TEXT, "QuestionId" INTEGER, "AcceptedAnswerId" INTEGER, PRIMARY KEY(Site, QuestionId))')
    create_table(database, "QuestionTags", 'CREATE TABLE "QuestionTags" ("Site" TEXT, "QuestionId" INTEGER, "Tags" TEXT, PRIMARY KEY(Site, QuestionId) )')
    create_table(database, "QuestionsMeta", 'CREATE TABLE "QuestionsMeta" ("Site" TEXT, "QuestionId" INTEGER, "CreationDate" TEXT, "ViewCount" INTEGER, "Score" INTEGER, "OwnerUserId" INTEGER, "AnswerCount" INTEGER, PRIMARY KEY(Site, QuestionId))')
    create_table(database, "QuestionsText", 'CREATE TABLE "QuestionsText" ("Site" TEXT, "QuestionId" INTEGER, "Title" TEXT, "Body" TEXT,  PRIMARY KEY(Site, QuestionId) )')
    #create_table(database, "RelatedQuestionsSource2Target", 'CREATE TABLE "RelatedQuestionsSource2Target" ( "QuestionId" INTEGER, "RelatedQuestionId" INTEGER, PRIMARY KEY(QuestionId, RelatedQuestionId))')
    #TODO: save sentences as list? use delimiter? or just use the one sentence and multiple occurances will be saved as multiple formulas?
    #create_table(database, "FormulaSentenceContext", 'CREATE TABLE "FormulaSentenceContext" ("FormulaId" INTEGER PRIMARY KEY, "Context" TEXT)')
    create_table(database, "SentenceContext", 'CREATE TABLE "SentenceContext" ("SentenceId" INTEGER PRIMARY KEY, "PostId" INTEGER, "Sentence" TEXT)')
    create_table(database, "FormulaSentence", 'CREATE TABLE "FormulaSentence" ("SentenceId" INTEGER, "FormulaId" INTEGER, PRIMARY KEY(SentenceId, FormulaId))')


#max_column_value("../output/mathematics.db", "FormulasComments", "FormulaId")