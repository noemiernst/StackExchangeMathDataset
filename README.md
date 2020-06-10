# Stack Exchange Dataset for Math Embeddings

Processing [stack exchange data dumps](https://archive.org/details/stackexchange) to a dataset in a database.

## Requirements

* **Python 3.7**
* [pandas](http://pandas.pydata.org/)
* [xml.etree.ElementTree](https://docs.python.org/2/library/xml.etree.elementtree.html)
* [cPickle or pickle](https://docs.python.org/3/library/pickle.html)
* matplotlib.pyplot
* sqlite3
* sklearn.feature_extraction.text -> CountVectorizer

## Dataset

### Usage

* download your interested Stack Exchange site data (*.stackexchange.com.7z) from [stack exchange data dump](https://archive.org/details/stackexchange), such as ```mathematics.stackexchange.com.7z``` or ```physics.stackexchange.com.7z
* unzip ```mathematics.stackexchange.com.7z``` to directory: ```dataset/mathematics```
* ```cd main```
* execute: ```python main.py --input ../input/ --dumps test_dumps --download yes --extract yes --output '../database/dataset.db'```

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
* tablename: Name of table to write topn contexts words of formulas in (will be overwritten if it exists)
    * default="FormulaContext"
* all: Get all words as context. This will lead to ignoring the values of input parameters for context and topn.
    * options: yes or no
    * default="no"

#### Outputs of ```context.py```

* The Context of the specified sites formulas will be saved in a database (```*.db```) as specified by the input parameter 'database' inside of the Table specified by the input parameter 'tablename'.
* Analysis/Statistics will be saved in file ```statistics.log``` in same directory as the database.

## ```statistics.py```

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

## ```context.py```

```main.py``` must previously been run for the dumps before running ```statistics.py```

#### Parameters of ```statistics.py```

* dumps: A text file containing a list of stackexchange dump sites names to be processed.
    * format: file containing a list of dump sites. Viable options can be found in the file /main/mathjax_dumps. The sites must already been processed into the database by running ```main.py``
    * default="test_dumps" in main directory
* database: Database file for data input.
    * default='../output/database.db'
* output: The output directory.
    * default='../output/'

#### Outputs of ```statistics.py```

* Directory '/diagrams/' in the output directory (as specified by the user) filled with diagrams of formula distributions for the sites specified by the user.
* HTML files displaying the diagram and some statistical values for each of the sites.

### How to unzip a *.7z file

* Install ```p7zip``` if not already installed: ```sudo apt-get install p7zip```
* To install the command line utility ```sudp atp-get install p7zip-full```
* Or [Install p7zip on Mac OSX](http://macappstore.org/p7zip/)
* execute command to extract a *.7z file: ```7za x *.7z```
