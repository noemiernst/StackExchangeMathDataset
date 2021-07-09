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
        p.append((start.tag, path, current.tag))
    if path != "":
        path += "|"
    for child in current.children:
        all_nodes = update_dict(all_nodes, child)
        p.extend(paths_td(start, path + current.tag, child, start_nodes, all_nodes))
        p.extend(paths_td(current, "", child, start_nodes, all_nodes))
    if not current.children:
        if current not in start_nodes:
            start_nodes.append(current)
            p.extend(paths_up(current, "", current, None, start_nodes, all_nodes))
    return p

def paths_up(start, path, current, prev, start_nodes, all_nodes):
    p = []
    if current != start:
        if all_nodes[start] < all_nodes[current]:
            p.append((start.tag, path, current.tag))
        if path != "":
            path += "|"
        if current.parent:
            all_nodes = update_dict(all_nodes, current.parent)
            p.extend(paths_up(start, path + current.tag, current.parent, current, start_nodes, all_nodes))
        for child in current.children:
            all_nodes = update_dict(all_nodes, child)
            if child is not prev:
                p.extend(paths_td(start, path + current.tag, child, start_nodes, all_nodes))
            '''if current not in start_nodes:
                start_nodes.append(current)
                p.extend(paths_up(current, "", current, None, start_nodes, all_nodes))'''
    else:
        if start.parent:
            all_nodes = update_dict(all_nodes, current.parent)
            p.extend(paths_up(start, path, start.parent, start, start_nodes, all_nodes))
            if start.parent not in start_nodes:
                start_nodes.append(start.parent)
                p.extend(paths_up(start.parent, "", start.parent, None, start_nodes, all_nodes))
        for child in start.children:
            all_nodes = update_dict(all_nodes, child)
            p.extend(paths_td(start, path, child, start_nodes, all_nodes))
    return p

def all_paths(symbolTree):
    p = []
    start = symbolTree.root
    while start.children:
        start = start.children[0]
    start_nodes = [start]
    all_nodes = {start : 0}

    # all paths
    p.extend(paths_up(start, "", start, None, start_nodes, all_nodes))

    # remove duplicates:
    p = list(dict.fromkeys(p))

    return p


def to_opt_tuples(opt_string):
    temp = SymbolTree.parse_from_opt(opt_string)

    paths = all_paths(temp)

    return paths

