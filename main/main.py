import argparse
from dump_processing.DumpDownloader import DumpDownloader
import os
import os.path
import libarchive.public
import pandas as pd
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
import sys

#TODO: update ReadMe

def save_hash(database, site, hash, exists):
    DB = sqlite3.connect(database)
    cursor = DB.cursor()

    if exists:
        cursor.execute("DELETE FROM SiteFileHash WHERE Site='" + site +"'")
    cursor.execute("INSERT INTO SiteFileHash (Site, MD5Hash)"
                   "VALUES ('" + site + "', '" + hash + "')")

    DB.commit()
    DB.close()

def extract_dumps(dump_directory, sites, extract):
    directories = []
    downloader = DumpDownloader()
    files = [os.path.join(dump_directory, downloader.get_file_name(site)) for site in sites]
    try:
        for file, site in zip(files, sites):
            output = file.replace(".7z", "/")
            directories.append(output)
            if extract == "yes":
                with libarchive.public.file_reader(file) as e:
                    print("extracting " + file + " to " + output + "...")
                    if not os.path.exists(output):
                        os.makedirs(output)
                    for entry in e:
                        with open(output + str(entry.pathname), 'wb') as f:
                            for block in entry.get_blocks():
                                f.write(block)
            elif extract == "no":
                if not os.path.exists(output):
                    raise OSError
                if (not os.path.exists(os.path.join(output, "Badges.xml"))) | (not os.path.exists(os.path.join(output, "Comments.xml"))) | \
                        (not os.path.exists(os.path.join(output, "PostLinks.xml"))) | (not os.path.exists(os.path.join(output, "Posts.xml"))) |\
                        (not os.path.exists(os.path.join(output, "Tags.xml"))):
                    raise OSError
            else:
                raise ValueError
    except ValueError:
        sys.exit("-x --extract value not valid. Possible values: 'yes' and 'no'")
    except OSError:
        sys.exit("Files or Directories missing. Extract dump files")

    return sites, directories, files

def dumps(dump_directory, filename_dumps, download, extract):
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

    return extract_dumps(dump_directory, sites, extract)

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

def main(dump_directory, filename_dumps, download, extract, database, force_process):
    start = time.time()
    log("../output/statistics.log", "#################################################")
    log("../output/statistics.log", "create_dataset.py")
    log("../output/statistics.log", "input: " + dump_directory)
    log("../output/statistics.log", "output: "+ database + ", ../output/statistics.log")
    log("../output/statistics.log", "dumps: " + filename_dumps)
    log("../output/statistics.log", "-------------------------")



    sites, directories, files = dumps(dump_directory, filename_dumps, download, extract)

    dump_processing.database.create_tables(database)

    DB = sqlite3.connect(database)
    sites_hashs = pd.read_sql('select * from "SiteFileHash"', DB)
    DB.close()

    bag_of_words = BOW()
    first = True

    for site, dir, file in zip(sites, directories, files):
        log("../output/statistics.log", "Processing site " + site)
        with open(file, 'rb') as f:
            hasher = hashlib.md5()
            for chunk in iter(lambda: f.read(128*hasher.block_size), b''):
                hasher.update(chunk)
            hash = hasher.hexdigest()
        exists = sites_hashs[sites_hashs["Site"] == site].any()[0]
        if exists:
            old_hash = sites_hashs["MD5Hash"][sites_hashs[sites_hashs["Site"] == site].index.values[0]]
        else:
            old_hash = ""
        if (hash != old_hash) | (force_process == "yes"):
            dump_processing.database.remove_site(site, database)
            dump_processing.process_dump.processing_main(site, dir, database, 7)
            save_hash(database,site, hash, exists)

    # calculate the idf scores of the corpus
    t = time.time()
    #bag_of_words.vectorize_corpus()
    log("../output/statistics.log", "time calculating idf scores: "+ str(int((time.time()-t)/60)) +"min " + str(int((time.time()-t)%60)) + "sec")
    log("../output/statistics.log", "max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")


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
    parser.add_argument("-x" ,"--extract", default="no", help="yes or no. Whether or not to extract the *.7z dump files")
    parser.add_argument("-o", "--output", default='../output/database.db', help="database output")
    parser.add_argument("-a", "--all", default="yes", help="yes or no. Force to process all dumps, even if they have previously been processed and already exist in the database")
    args = parser.parse_args()
    main(args.input, args.dumps, args.download, args.extract, args.output, args.all)
