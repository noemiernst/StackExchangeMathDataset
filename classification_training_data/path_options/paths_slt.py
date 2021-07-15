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
        p.append((start.tag.split("#")[1], path, current.tag.split("#")[1]))
    for child in current.children:
        # for all children, keep walking down
        position = [child.tag.split("#")[0]]
        all_nodes = update_dict(all_nodes, child)
        p.extend(paths_td(start, path + [current.tag.split("#")[1]] + position, child, start_nodes, all_nodes))
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
            p.append((start.tag.split("#")[1], path, current.tag.split("#")[1]))
        if current.parent:
            # if there is a parent, keep walking up
            position = [current.tag.split("#")[0]]
            all_nodes = update_dict(all_nodes, current.parent)
            p.extend(paths_up(start, path + [current.tag.split("#")[1]] + position, current.parent, current, start_nodes, all_nodes))
        for child in current.children:
            # for all children (except previous where we just walked up from), walk down
            position = [child.tag.split("#")[0]]
            all_nodes = update_dict(all_nodes, child)
            if child is not prev:
                p.extend(paths_td(start, path + [current.tag.split("#")[1]] + position, child, start_nodes, all_nodes))
    else:
        # for starting node
        if start.parent:
            # if there is a parent node, walk up
            position = [start.tag.split("#")[0]]
            all_nodes = update_dict(all_nodes, current.parent)
            p.extend(paths_up(start, path + position, start.parent, start, start_nodes, all_nodes))
            # and use parent node as starting node
            if start.parent not in start_nodes:
                start_nodes.append(start.parent)
                p.extend(paths_up(start.parent, [], start.parent, None, start_nodes, all_nodes))
        # for all children walk down
        for child in start.children:
            position = [child.tag.split("#")[0]]
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

def reverse_tuples(tuples):
    r = []
    for start, path, target in tuples:
        path.reverse()
        r.append((target, path, start))
    return r

def parse_tree(pos, layoutTree):
    semanticTree = SemanticSymbol(pos + "#" + layoutTree.tag)
    children = []
    for child in layoutTree.active_children():
        children.append(parse_tree(child[0], child[1]))
    for child in children:
        child.parent = semanticTree
    semanticTree.children = children

    return semanticTree

def all_paths(symbolTree):
    p = []
    semanticTree = parse_tree("root", symbolTree.root)
    start = semanticTree
    while start.children:
        start = start.children[0]
    start_nodes = [start]
    all_nodes = {start : 0}

    # all paths
    p.extend(paths_up(start, [], start, None, start_nodes, all_nodes))

    # remove duplicates:
    #p = list(dict.fromkeys(p))
    p = remove_duplicates(p)

    p = reverse_tuples(p)

    return p


def to_slt_tuples(slt_string):
    temp = SymbolTree.parse_from_slt(slt_string)

    paths = all_paths(temp)

    return paths


#to_slt_tuples('[V!Q,b[V!n[+[N!1]]]]')
#to_slt_tuples('[V!I[M!()1x1,w[V!x]],b[V!n[=[N!0]]]]')
