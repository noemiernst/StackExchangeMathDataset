# check validity of test/train/val files
# each line:
# <labels> <paths>
# where <labels> is list of labels separated by a | label_1|...|label_n
# and <paths> ist list of paths separated by a space <path1> <path2> ... <path_m>
# a <path> is a triple separated by commas: start,<p>,end
# the <p> is a list of path segments separated by a | edge1|edge2|...

def check(line):
    chunks = line.split()
    labels = chunks[0]
    valid_labels = check_labels(labels)
    paths = chunks[1:]
    valid_paths = check_paths(paths)
    return valid_labels and valid_paths

def check_labels(labels):
    labels_list = labels.split("|")
    if len(labels_list) < 1:
        return False
    return True

def check_paths(paths):
    for path in paths:
        if path == "":
            return True
        if " " in path:
            return False
        temp = path.split(",")
        if len(temp) != 3:
            return False
        p = temp[1].split("|")
        if len(p) < 1:
            return False
        if len(p) > 8:
            return False
    return True


"""
# read file
file = open(file_name, 'r')
invalid_count = 0
line_count = 0
invalid_lines = []
for line in file:
    v = check(line)
    line_count += 1
    if not v:
        print(line)
        invalid_count +=1
        invalid_lines.append(line_count)
file.close()
print("number of invalid lines:" + str(invalid_count))
print("invalid lines: " + str(invalid_lines))

file = open(file_name_new, 'w')
file.close()
file = open(file_name, 'r')
lines = file.readlines()
file.close()

file = open(file_name_new, 'w')
for number, line in enumerate(lines):
    if number not in invalid_lines:
        file.write(line)
file.close()
"""
