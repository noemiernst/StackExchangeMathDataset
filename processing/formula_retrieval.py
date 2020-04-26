import argparse
import os.path
from processing.process_posts import posts_processing

def processing_main(dir_name, database_name):
    posts_processing(dir_name, database_name)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i","--input",default= "../dataset/mathematics", help = "input directory of stackexchange dump *.xml files")
    parser.add_argument("-d", "--database", default='../database/dataset.db', help="output database")
    args = parser.parse_args()
    processing_main(args.input, args.database)
