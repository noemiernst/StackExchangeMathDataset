import urllib.request
import os.path
import time


class DumpDownloader:
    # sites that use mathjax as of 08/05/2020
    sites_with_mathjax = ["3dprinting", "ham", "ai", "astronomy", "aviation", "bioinformatics", "biology", "blender", "chemistry",
             "codegolf", "codereview", "scicomp", "computergraphics", "cs", "cseducators", "stats", "crypto",
             "datascience", "earthscience", "economics", "electronics", "engineering", "gamedev", "hsm",
             "mathoverflow", "mathematica", "math", "matheducators", "or", "physics", "puzzling",
             "quant", "quantumcomputing", "robotics", "rpg", "dsp", "space", "cstheory", "worldbuilding"]
    downloads = {"3dprinting": "3dprinting.stackexchange.com.7z",
                 "ham": "ham.stackexchange.com.7z",
                 "ai": "ai.stackexchange.com.7z",
                 "astronomy": "astronomy.stackexchange.com.7z",
                 "aviation": "aviation.stackexchange.com.7z",
                 "bioinformatics": "bioinformatics.stackexchange.com.7z",
                 "biology": "biology.stackexchange.com.7z",
                 "blender": "blender.stackexchange.com.7z",
                 "chemistry": "chemistry.stackexchange.com.7z",
                 "codegolf": "codegolf.stackexchange.com.7z",
                 "codereview": "codereview.stackexchange.com.7z",
                 "scicomp": "scicomp.stackexchange.com.7z",
                 "computergraphics": "computergraphics.stackexchange.com.7z",
                 "cs": "cs.stackexchange.com.7z",
                 "cseducators": "cseducators.stackexchange.com.7z",
                 "stats": "stats.stackexchange.com.7z",
                 "crypto": "crypto.stackexchange.com.7z",
                 "datascience": "datascience.stackexchange.com.7z",
                 "earthscience": "earthscience.stackexchange.com.7z",
                 "economics": "economics.stackexchange.com.7z",
                 "electronics": "electronics.stackexchange.com.7z",
                 "engineering": "engineering.stackexchange.com.7z",
                 "gamedev": "gamedev.stackexchange.com.7z",
                 "hsm": "hsm.stackexchange.com.7z",
                 "mathoverflow": "mathoverflow.net.7z",
                 "mathematica": "mathematica.stackexchange.com.7z",
                 "math": "math.stackexchange.com.7z",
                 "matheducators": "matheducators.stackexchange.com.7z",
                 "or": "or.stackexchange.com.7z",
                 "physics": "physics.stackexchange.com.7z",
                 "puzzling": "puzzling.stackexchange.com.7z",
                 "quant": "quant.stackexchange.com.7z",
                 "quantumcomputing": "quantumcomputing.stackexchange.com.7z",
                 "robotics": "robotics.stackexchange.com.7z",
                 "rpg": "rpg.stackexchange.com.7z",
                 "dsp": "dsp.stackexchange.com.7z",
                 "space": "space.stackexchange.com.7z",
                 "cstheory": "cstheory.stackexchange.com.7z",
                 "worldbuilding": "worldbuilding.stackexchange.com.7z"}
    special_delim = {"codegolf": r'\$',
                     "codereview": r'\$',
                     "electronics": r'\$',
                     "gamedev": r'\$',
                     "rpg": r'\$'}
    mhchem ={"biology": r'\ce{',
             "chemistry": r'\ce{',
             "earthscience": r'\ce{'}
    archive_stackexchange_dumps_url = "https://archive.org/download/stackexchange/"

    def download(self, url, file_name):
        t = time.time()
        print("downloading "+ url)
        # Download the file from `url` and save it locally under `file_name`:
        urllib.request.urlretrieve(url, file_name)
        print("file saved at " + file_name)
        print("file size: ~"+ str(int(os.path.getsize(file_name)/(1000000))) + "MB")
        print("download time: " + format(time.time()-t, ".2f")+ "s")

    def download_all_mathjax(self, directory):
        t = time.time()
        for site in self.sites_with_mathjax:
            file = self.downloads[site]
            self.download(self.archive_stackexchange_dumps_url + file, os.path.join(directory, file))
        print("total download time: " + str(int((time.time()-t)/60))+ "min " + str(int(time.time()-t)%60)+ "sec")

    def download_some(self, directory, some):
        t = time.time()
        for site in some:
            if self.downloads.keys().__contains__(site):
                file = self.downloads[site]
                self.download(self.archive_stackexchange_dumps_url + file, os.path.join(directory, file))
        print("total download time: " + str(int((time.time()-t)/60))+ "min " + str(int(time.time()-t)%60)+ "sec")

    def get_mathjax_sites(self):
        return self.sites_with_mathjax

    def get_mathjax_file_names(self):
        return self.downloads.values()

    def get_file_name(self, site):
        return self.downloads[site]
