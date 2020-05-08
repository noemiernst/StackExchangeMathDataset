import urllib.request
import os.path
import time


class DumpDownloader:
    # sites that use mathjax as of 08/05/2020
    sites_with_mathjax = ["3dprinting", "ham", "ai", "astronomy", "aviation", "bioinformatics", "biology", "blender", "chemistry",
             "codegolf", "codereview", "scicomp", "computergraphics", "cs", "cseducators", "stats", "crypto",
             "datascience", "earthscience", "economics", "electronics", "engineering", "gamedev", "hsm", "materials",
             "mathoverflow", "mathematica", "math", "matheducators", "or", "physics", "psychology", "puzzling",
             "quant", "quantumcomputing", "robotics", "rpg", "dsp", "space", "cstheory", "worldbuilding"]
    archive_stackexchange_dumps_url = "https://archive.org/download/stackexchange/"

    def download(self, url, file_name):
        t = time.time()
        print("downloading "+ url)
        # Download the file from `url` and save it locally under `file_name`:
        urllib.request.urlretrieve(url, file_name)
        print("file saved at " + file_name)
        print("download time: " + format(time.time()-t, ".2f")+ "s")

    def download_all_mathjax(self, directory):
        t = time.time()
        for site in self.sites_with_mathjax:
            file = site + ".stackexchange.com.7z"
            self.download(self, self.archive_stackexchange_dumps_url + file, os.path.join(directory, file))
        print("total download time: " + str(int((time.time()-t)/60))+ "min " + str(int(time.time()-t)%60)+ "sec")


dwn = DumpDownloader
file = "ai" + ".stackexchange.com.7z"
dwn.download_all_mathjax(dwn, "downloads")
