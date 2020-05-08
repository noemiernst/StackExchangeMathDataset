def log(file,line):
    print(line)
    with open(file,"a") as f:
        f.write("%s \n" % line)
