# Stack Exchange Dataset of Mathematical Formulas

Processing [stack exchange data dumps](https://archive.org/details/stackexchange) to a dataset of mathematical formulas

## Requirements

* **Python 3.7**

##### Python Packages
Install python packages by running: ```pip install -r requirements.txt```
* [pandas](http://pandas.pydata.org/)
* [xml.etree.ElementTree](https://docs.python.org/2/library/xml.etree.elementtree.html)
* [cPickle or pickle](https://docs.python.org/3/library/pickle.html)
* [matplotlib](https://matplotlib.org/users/installing.html)
* [sqlite3](https://docs.python.org/3/library/sqlite3.html)
* [scikit_learn](https://scikit-learn.org/stable/install.html)
* [libarchive](https://pypi.org/project/libarchive/)

##### Other tools
* [LaTeXML](https://dlmf.nist.gov/LaTeXML/get.html)

## Dataset

### Creating the Dataset

* ```cd main```
* execute: ```python main.py --input ../input/ --dumps test_dumps --download yes --extract yes --output ../output/database.db```
* execute (only after main.py has been executed): ```python context.py --input ../input/ --dumps test_dumps --download yes --database ../output/database.db --context 10 --topn 3 --tablename FormulaContext```
* execute (only after main.py has been executed): ```python statistics.py --dumps test_dumps --database ../output/database.db --output ../output/```

### Using the Dataset

The data from the database can be accessed via SQL commands, e.g.:
```
sqlite3
.open output/database.db
SELECT * FROM FormulasPosts WHERE FormulaId="5783548";
SELECT Site, Tag FROM Tags WHERE Count>"1500";
SELECT AnswerText.Site, AnswerText.AnswerId, AnswerText.Body 
   FROM AnswerText INNER JOIN AnswerMeta ON AnswerText.Site=AnswerMeta.Site 
   AND AnswerText.AnswerId=AnswerMeta.AnswerId AND AnswerMeta.Score="100";
SELECT max(Score) FROM QuestionMeta;
```

## ```main.py```

#### Parameters of ```main.py```

* input: Input directory of stackexchange dump *.7z files. Where they are or where there should be downloaded to. 
    * default= "../input/"
* dumps: A text file containing a list of stackexchange dump sites names to be processed.
    * format: file containing a list of dump sites. Viable options can be found in the file /main/mathjax_dumps.
    * default="test_dumps" in main directory
* download: Whether or not the program should download the dumps.
    * options: yes or no
    * default="yes"
* extract: Whether or not to extract the *.7z dump files.
    * options: yes or no
    * default="yes"
* output: database output
    * default='../output/database.db'
* all: Force to process all dumps, even if they have previously been processed and already exist in the database.
    * options: yes or no
    * default="no"

#### Outputs of ```main.py```

* The Dataset will be saved in a database (```*.db```) as specified by the input parameter 'output'.
* Analysis/Statistics will be saved in file ```statistics.log``` in same directory as the database.

![Alt text](images/Schema_Bezier_noGrid_color.png "Database after running ```main.py```")

## ```context.py```

```main.py``` must previously been run for the dumps before running ```context.py```

#### Parameters of ```context.py```

* input: Input directory of stackexchange dump files and directories 
    * default= "../input/"
* dumps: A text file containing a list of stackexchange dump sites names to be processed.
    * format: file containing a list of dump sites. Viable options can be found in the file /main/mathjax_dumps. The sites must already been processed into the database by running ```main.py``
    * default="test_dumps" in main directory
* database: database input and output
    * default='../output/database.db'
* context: The number of words around formula to be reagarded as possible context.
    * options: an integer
    * default="10"
* topn: The number of top terms in context regarding their tf-idf scores to be retrieved as formula context.
    * default='3'
* corpus: Whether the corpus for idf ratings should be calculated over all sites or individually for each site.
    * options: all or individual
    * default="all"
* stopwords: Whether or not to use stopwords and which ones to use
  * Options: none, english, or filename containing list of stopwords (e.g. stopwords). 'english' is the english stopword list of the nltk toolkit
  * default="stopwords"
* tfidf: Whether or not to show tf-idf ratings with top context words
  * options: yes, no
  * default="yes"
* tablename: Name of table to write topn contexts words of formulas in (will be overwritten if it exists)
    * default="FormulaContext"
* all: Get all words as context. This will lead to ignoring the values of input parameters for context and topn.
    * options: yes or no
    * default="no"

#### Outputs of ```context.py```

* The Context of the specified sites formulas will be saved in a database (```*.db```) as specified by the input parameter 'database' inside of the Table specified by the input parameter 'tablename'.
* Analysis/Statistics will be saved in file ```statistics.log``` in same directory as the database.

![Alt text](images/Schema_Formulas.png "Table created with ```context.py``` (blue) and tables created with ```parse_formulas.py``` (red)")

## ```parse_formulas.py```

```main.py``` must previously been run for the dumps before running ```parse_formulas.py```.

```parse_formulas.py``` will only parse formulas that have not been parsed due to the long runtime of LaTeXML.

#### Parameters of ```parse_formulas.py```

* dumps: A text file containing a list of stackexchange dump sites names to be processed.
    * format: file containing a list of dump sites. Viable options can be found in the file /main/mathjax_dumps. The sites must already been processed into the database by running ```main.py``
    * default="test_dumps" in main directory
* database: database input and output
    * default='../output/database.db'
* mode: parse formulas in ContentMathML (cmml), PresentationMathML (pmml), or both
  * options: cmml, pmml, both

#### Outputs of ```parse_formulas.py```

* The ContentMathML and/or PresentationMathML of the specified sites formulas will be saved in the database (```*.db```) as specified by the input parameter 'database' inside of the Tables 'FormulasPostsMathML' and 'FormulasCommentsMathML'.
* Analysis/Statistics will be saved in file ```statistics.log``` in same directory as the database.

## ```statistics.py```

```main.py``` must previously been run for the dumps before running ```statistics.py```

#### Parameters of ```statistics.py```

* dumps: A text file containing a list of stackexchange dump sites names to be processed.
    * format: file containing a list of dump sites. Viable options can be found in the file /main/mathjax_dumps. The sites must already been processed into the database by running ```main.py``
    * default='test_dumps' in main directory
* database: Database file for data input.
    * default='../output/database.db'
* output: The output directory.
    * default='../output/'

#### Outputs of ```statistics.py```

* Directory '/diagrams/' in the output directory (as specified by the user) filled with diagrams of formula distributions for the sites specified by the user.
* HTML files displaying the diagram and some statistical values for each of the sites.

