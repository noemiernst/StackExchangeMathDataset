# FormulaRetrieval

Processing [stack exchange data dump](https://archive.org/details/stackexchange) to a dataset for fomula retrieval

## Requirements

* **Python 3.7**
* [pandas](http://pandas.pydata.org/)
* [xml.etree.ElementTree](https://docs.python.org/2/library/xml.etree.elementtree.html)
* [cPickle or pickle](https://docs.python.org/3/library/pickle.html)

## Formula_Retrieval

### Usage

* download your interested Stack Exchange site data (*.stackexchange.com.7z) from [stack exchange data dump](https://archive.org/details/stackexchange), such as ```mathematics.stackexchange.com.7z```
* unzip ```mathematics.stackexchange.com.7z``` to directory: ```dataset/mathematics```
* ```cd processing```
* execute: ```python formula_retrieval.py --input ../dataset/mathematics/ --database '../database/dataset.db'```

#### Parameters of ```formula_retrieval.py```

* input: file directory which saves Posts.xml, PostLinks.xml, Votes.xml, Badges.xml, and Comments.xml. In above example, input is ```dataset/mathematics```
* database: file of output database
* 
#### Outputs of ```formula_retrieval.py```

* Outputs will be saved in ```.db```.
* Analysis/Statistics will be saved in file ```statistics.log```.

### How to unzip a *.7z file

* Install ```p7zip``` if not already installed: ```sudo apt-get install p7zip```
* To install the command line utility ```sudp atp-get install p7zip-full```
* Or [Install p7zip on Mac OSX](http://macappstore.org/p7zip/)
* execute command to extract a *.7z file: ```7za x *.7z```
