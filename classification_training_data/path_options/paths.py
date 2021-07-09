from classification_training_data.math_tan.symbol_tree import SymbolTree
from classification_training_data.math_tan.symbol_tree import SemanticSymbol

def update_dict(dict, new_key):
    if new_key not in dict.keys():
        dict[new_key] = len(dict.keys())
    return dict

# all paths top down
def paths_td(start, path, current, start_nodes, all_nodes):
    p = []
    if all_nodes[start] < all_nodes[current]:
        # add the current path
        p.append((start.tag, path, current.tag))
    for child in current.children:
        # for all children, keep walking down
        position = []
        if current.tag[0] != "U":
            position = [current.children.index(child)]
        all_nodes = update_dict(all_nodes, child)
        p.extend(paths_td(start, path + [current.tag] + position, child, start_nodes, all_nodes))
        # use current node to start newly and walk down
        p.extend(paths_td(current,[] + position, child, start_nodes, all_nodes))
    if not current.children:
        # if there is no children, use current node to start walking up
        if current not in start_nodes:
            start_nodes.append(current)
            p.extend(paths_up(current, [], current, None, start_nodes, all_nodes))
    return p

def paths_up(start, path, current, prev, start_nodes, all_nodes):
    p = []
    if current != start:
        if all_nodes[start] < all_nodes[current]:
            # add the current path
            p.append((start.tag, path, current.tag))
        if current.parent:
            # if there is a parent, keep walking up
            position = []
            if current.parent.tag[0] != "U":
                position = [current.parent.children.index(current)]
            all_nodes = update_dict(all_nodes, current.parent)
            p.extend(paths_up(current, path + [current.tag] + position, current.parent, current, start_nodes, all_nodes))
        for child in current.children:
            # for all children (except previous where we just walked up from), walk down
            position = []
            if current.tag[0] != "U":
                position = [current.children.index(child)]
            all_nodes = update_dict(all_nodes, child)
            if child is not prev:
                p.extend(paths_td(start, path + [current.tag] + position, child, start_nodes, all_nodes))
    else:
        # for starting node
        if start.parent:
            # if there is a parent node, walk up
            position = []
            if start.parent.tag[0] != "U":
                position = [start.parent.children.index(start)]
            all_nodes = update_dict(all_nodes, current.parent)
            p.extend(paths_up(start, path + position, start.parent, start, start_nodes, all_nodes))
            # and use parent node as starting node
            if start.parent not in start_nodes:
                start_nodes.append(start.parent)
                p.extend(paths_up(start.parent, [], start.parent, None, start_nodes, all_nodes))
        # for all children walk down
        for child in start.children:
            position = []
            if start.tag[0] != "U":
                position = [start.children.index(child)]
            all_nodes = update_dict(all_nodes, child)
            p.extend(paths_td(start, path + position, child, start_nodes, all_nodes))
    return p

def remove_duplicates(tuples):
    # tuples: (start, [path], target)
    d = {}
    for start, path, target in tuples:
        if (start, target) not in d.keys():
            d[(start, target)] = [path]
        else:
            if d[(start, target)][0] != path:
                d[(start, target)].append(path)
    tuples = []
    for key in d.keys():
        for path in d[key]:
            tuples.append((key[0], path, key[1]))
    return tuples

def all_paths(symbolTree):
    p = []
    start = symbolTree.root
    while start.children:
        start = start.children[0]
    start_nodes = [start]
    all_nodes = {start : 0}

    # all paths
    p.extend(paths_up(start, [], start, None, start_nodes, all_nodes))

    # remove duplicates:
    #p = list(dict.fromkeys(p))
    p = remove_duplicates(p)

    return p


def to_opt_tuples(opt_string):
    temp = SymbolTree.parse_from_opt(opt_string)

    paths = all_paths(temp)

    return paths


#to_opt_tuples('[U!eq,0[V!𝑙],1[O!divide,0[O!SUB,0[V!𝑉],1[V!𝑚]],1[O!SUB,0[V!𝐴],1[V!𝑑]]]]')
#to_opt_tuples('[U!eq,0[V!𝑙],1[O!SUB,0[V!𝑉],1[V!𝑚]]]')


'''
def to_slt_tuples(slt_string):
    temp = SymbolTree.parse_from_slt(slt_string)

    paths = all_paths(temp)

    return paths


string = '[V!Q,b[V!n[+[N!1]]]]'
string2 = '[V!I[M!()1x1,w[V!x]],b[V!n[=[N!0]]]]'

to_slt_tuples(string)
to_slt_tuples(string2)
'''
