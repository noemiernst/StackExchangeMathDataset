import argparse
from DumpDownloader import DumpDownloader
import os
import os.path
import libarchive.public
#TODO pip install libarchive

import dump_processing.database
import dump_processing.process_dump
from dump_processing.helper import log
import time
import resource
import context_processing.process_context


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
    return sites, directories

def dumps(dump_directory, filename_dumps, download):
    with open(filename_dumps) as f:
        sites = [line.rstrip() for line in f if line is not ""]
    if download is "yes":
        downloader = DumpDownloader()
        downloader.download_some(dump_directory, sites)
    elif download is "no":
        for site in sites:
            file = os.path.join(dump_directory, site + ".stackexchange.com.7z")
            if os.path.isfile(file):
                pass
            else:
                raise FileNotFoundError(file + " not found in " + dump_directory)
    else:
        raise ValueError("Invalid argument 'download'")

    return extract_dumps(dump_directory, sites)

def main(dump_directory, filename_dumps, download, database):
    start = time.time()
    log("../output/statistics.log", "#################################################")
    log("../output/statistics.log", "create_dataset.py")
    log("../output/statistics.log", "input: " + dump_directory)
    log("../output/statistics.log", "output: "+ database + ", ../output/statistics.log")
    log("../output/statistics.log", "dumps: " + filename_dumps)
    log("../output/statistics.log", "-------------------------")

    sites, directories = dumps(dump_directory, filename_dumps, download)

    dump_processing.database.create_tables(database)

    for site, dir in zip(sites, directories):
        # TODO:
        #  do further processing with pickles questiontext, answertext and commenttext in directory of database
        #  update readme
        dump_processing.process_dump.processing_main(site, dir, database)
        context_processing.process_context.context_main(site, database)


    # TODO:
    #  keyword extraction (via tf-idf)
    #  need corpus (of all sites texts?)
    #  extract keywords from all texts of each site
    #  get only context around formulas?

    # TODO
    #  context only as BOW?
    #  corpus of all sites text? or each site? or even seperate posts and comments?

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
