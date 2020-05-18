import argparse
from DumpDownloader import DumpDownloader
import os
import os.path
import libarchive.public
#TODO pip install libarchive


def extract_dumps(dump_directory, sites):
    files = [os.path.join(dump_directory, site + ".stackexchange.com.7z") for site in sites]
    for file, site in zip(files, sites):
        with libarchive.public.file_reader(file) as e:
            output = os.path.join(dump_directory, site + ".stackexchange.com/")
            print("extracting " + file + " to " + output + "...")
            if not os.path.exists(output):
                os.makedirs(output)
            for entry in e:
                with open(output + str(entry.pathname), 'wb') as f:
                    for block in entry.get_blocks():
                        f.write(block)

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
    extract_dumps(dump_directory, sites)

def main(dump_directory, filename_dumps, download, database):
    dumps(dump_directory, filename_dumps, download)




if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i","--input",default= "../input/", help = "input directory of stackexchange dump *.7z files")
    parser.add_argument("-d", "--dumps",default="test_dumps", help="File containing stackexchange dump sites names to be processed")
    parser.add_argument("--download", default="no", help="yes or no. Whether or not to download all dumps")
    parser.add_argument("-o", "--output", default='../output/database.py', help="database output")
    args = parser.parse_args()
    main(args.input, args.dumps, args.download, args.output)
