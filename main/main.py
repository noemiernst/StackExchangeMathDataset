import argparse
from dump_processing.DumpDownloader import DumpDownloader
import os
import os.path
import libarchive.public
try:
    import cPickle as pickle
except ImportError:
    import pickle
#TODO pip install libarchive
# pip install hashlib?

import dump_processing.database
import dump_processing.process_dump
from dump_processing.helper import log
import time
import resource
from context_processing.BOW import BOW
import pathlib
import hashlib
import sqlite3

#TODO: update ReadMe

def get_hash(database, site):
    DB = sqlite3.connect(database)
    cursor = DB.cursor()

    cursor.execute("SELECT MD5Hash FROM SiteFileHash WHERE site='" + site + "'")

    DB.commit()
    DB.close()

    #if the count is 1, then table exists
    if cursor.fetchone()[0]:
        return True, cursor.fetchone()
    return False, ""

def save_hash(database, site, hash, exists):
    DB = sqlite3.connect(database)
    cursor = DB.cursor()

    if exists:
        cursor.execute("DELETE FROM MD5Hash WHERE site='" + site +"'")
    cursor.execute("INSERT INTO MD5Hash (" + site +"," + hash + ")")

    DB.commit()
    DB.close()

    #if the count is 1, then table exists
    if cursor.fetchone()[0]:
        return cursor.fetchone()
    return ""


def extract_dumps(dump_directory, sites):
    directories = []
    downloader = DumpDownloader()
    files = [os.path.join(dump_directory, downloader.get_file_name(site)) for site in sites]
    for file, site in zip(files, sites):
        with libarchive.public.file_reader(file) as e:
            output = file.replace(".7z", "/")
            directories.append(output)
            print("extracting " + file + " to " + output + "...")
            if not os.path.exists(output):
                os.makedirs(output)
            for entry in e:
                with open(output + str(entry.pathname), 'wb') as f:
                    for block in entry.get_blocks():
                        f.write(block)
    return sites, directories, files

def dumps(dump_directory, filename_dumps, download):
    with open(filename_dumps) as f:
        sites = [line.rstrip() for line in f if line is not ""]
    downloader = DumpDownloader()
    if download is "yes":
        downloader.download_some(dump_directory, sites)
    elif download is "no":
        for site in sites:
            file = os.path.join(dump_directory, downloader.get_file_name(site))
            if os.path.isfile(file):
                pass
            else:
                raise FileNotFoundError(file + " not found in " + dump_directory)
    else:
        raise ValueError("Invalid argument 'download'")

    return extract_dumps(dump_directory, sites)

def cleanup(sites, directories):
    try:
        os.remove(os.path.join(pathlib.Path(directories[0]).parent.absolute(), "corpus.pkl"))
    except OSError:
        pass
    except ValueError:
        pass

    for dir in directories:
        try:
            os.remove(os.path.join(dir, "questiontext.pkl"))
            os.remove(os.path.join(dir, "answertext.pkl"))
            os.remove(os.path.join(dir, "commenttext.pkl"))
            os.remove(os.path.join(dir, "formulacontext.pkl"))
        except OSError:
            pass

def main(dump_directory, filename_dumps, download, database):
    start = time.time()
    log("../output/statistics.log", "#################################################")
    log("../output/statistics.log", "create_dataset.py")
    log("../output/statistics.log", "input: " + dump_directory)
    log("../output/statistics.log", "output: "+ database + ", ../output/statistics.log")
    log("../output/statistics.log", "dumps: " + filename_dumps)
    log("../output/statistics.log", "-------------------------")


    hasher = hashlib.md5()

    sites, directories, files = dumps(dump_directory, filename_dumps, download)

    dump_processing.database.create_tables(database)

    bag_of_words = BOW()
    first = True

    for site, dir, file in zip(sites, directories, files):
        log("../output/statistics.log", "Processing site " + site)
        with open(file, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
            hash = hasher.hexdigest()
        old_hash, exists = get_hash(database, site)
        if hash != old_hash:
            dump_processing.database.remove_site(site)
            dump_processing.process_dump.processing_main(site, dir, database, 7)
            save_hash(database,site, hash, exists)

        #bag_of_words.corpus_from_pickles(dir, not first)
        #first = False

    # calculate the idf scores of the corpus
    t = time.time()
    bag_of_words.vectorize_corpus()
    log("../output/statistics.log", "time calculating idf scores: "+ str(int((time.time()-t)/60)) +"min " + str(int((time.time()-t)%60)) + "sec")
    log("../output/statistics.log", "max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")

    # calculate tf-idf scores for all sites contents
    # for each post/comment or formulas surrounding words?
    for dir in directories:
        with open(os.path.join(dir, "formulacontext.pkl"),"rb") as f:
            formula_context_dict = pickle.load(f)
        top_n_context = bag_of_words.get_top_n_tfidf(formula_context_dict.values(), 3)

        #TODO: save in database
        #TODO: improve runtime if possible


    # TODO: highlighted, bold etc words

    # delete all pkl files created during dump processing
    #cleanup(sites, directories)

    log("../output/statistics.log", "-------------------------")
    log("../output/statistics.log", "total execution time: "+ str(int((time.time()-start)/60)) +"min " + str(int((time.time()-start)%60)) + "sec")
    log("../output/statistics.log", "max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")
    log("../output/statistics.log", "#################################################")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i","--input",default= "../input/", help = "input directory of stackexchange dump *.7z files")
    parser.add_argument("-d", "--dumps",default="test_dumps", help="File containing stackexchange dump sites names to be processed")
    parser.add_argument("--download", default="no", help="yes or no. Whether or not to download the dumps")
    parser.add_argument("-o", "--output", default='../output/database.db', help="database output")
    args = parser.parse_args()
    main(args.input, args.dumps, args.download, args.output)
