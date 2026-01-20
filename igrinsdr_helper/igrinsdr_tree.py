import astrodata
import igrins_instruments
# import igrinsdr

from pathlib import Path
from itertools import groupby, tee
from operator import itemgetter

from collections import namedtuple
MyNode = namedtuple("MyNode", ["label", "children"])
from rich import print as rprint

def convert_markup(label):
    """Convert simple HTML-like markup to Textual markup."""
    # Remove single quotes that might be around labels from the original helper
    label = label.strip("'")
    return label.replace("<b>", "[b]").replace("</b>", "[/b]")

# rootdir = Path("indata/20240425")
# fn_list, tags_list = [], []

def _get_ad_tree(paths):
    ads = (astrodata.open(fn) for fn in sorted(paths))
    obsid_tags = [(ad.filename, ad.observation_id() + " - " + ad.object(), ad.tags,
                   str(ad.exposure_time())+"s")
                  for ad in ads]
    all_tags = [_[2] for _ in obsid_tags]

    root_common_tags = set.intersection(*all_tags)
    # nodes = []
    root = MyNode("'{}'".format(" ".join(root_common_tags)), [])
    for k, grouped in groupby(obsid_tags, itemgetter(1)):
        grouped1, grouped2 = tee(grouped, 2)
        group_tags = [_[2].difference(root_common_tags) for _ in grouped1]
        group_common_tags = set.intersection(*group_tags)
        group_nodes = [(g[0], tags.difference(group_common_tags), g[3])
                       for g, tags in zip(grouped2, group_tags)]

        bold_tags = group_common_tags.intersection(["FLAT", "SKY", "SCIENCE", "STANDARD"])
        normal_tags = group_common_tags.difference(bold_tags)
        if bold_tags:
            tt = "<b>{}</b> {}".format(" ".join(bold_tags), " ".join(normal_tags))
        else:
            tt = " ".join(normal_tags)

        n = MyNode(f"'{tt}' : {k}", [])
        root.children.append(n)

        for s, subgroups in groupby(group_nodes, lambda o: (o[1], o[2])):
            ss = list(subgroups)
            if len(ss) > 1:
                label = "<b>'{}' x {}</b> : {} .. {}".format(" ".join(list(s[0]) + [s[1]]),
                                                             len(ss), ss[0][0], ss[-1][0])
                n.children.append(MyNode(label, [MyNode(s1[0], []) for s1 in ss]))
            else:
                label = "<b>'{}' x 1</b> : '{}'".format(" ".join(list(s[0]) + [s[1]]), ss[0][0])
                n.children.append(MyNode(label, []))
    return root

from ipytree import Tree, Node

def make_node(node, i):
    if i == 1:
        kw = dict(icon_style="success")
    elif i == 2:
        kw = dict(icon_style="warning")
    elif i == 3:
        kw = dict(opened=False)
    else:
        kw = dict()
    return Node(node.label, [make_node(n, i+1) for n in node.children], **kw)

def make_tree(node):

    tree = Tree(stripes=True)

    tree.add_node(make_node(node, 1))

    return tree


def _collect_simple_tree_lines(node, lines, level=0, max_level=None):
    indent = "  " * level
    
    # Add icon/color based on level (matching TUI logic)
    icon = ""
    if level == 0:
        icon = "[green]\u25cf[/] " # Circle
    elif level == 1:
        icon = "[yellow]\u25cb[/] " # Empty circle
    
    # Convert markup to Rich/Textual format
    clean_label = convert_markup(node.label)
    
    # Add to lines buffer
    lines.append(f"{indent}- {icon}{clean_label}")
    
    if max_level is not None and level >= max_level:
        return

    for child in node.children:
        _collect_simple_tree_lines(child, lines, level + 1, max_level)

def print_simple_tree(node, level=0, max_level=None):
    lines = []
    _collect_simple_tree_lines(node, lines, level, max_level)
    rprint("\n".join(lines))


def get_ad_tree(paths, sort=True, simple=False):
    if sort:
        paths = sorted(paths)
    
    root_node = _get_ad_tree(paths)

    if simple:
        # User requested simple output mode logic
        # Default behavior of TUI is expanding level 1 and 2 (root + groups)
        # So we set max_level=2 by default for this convenience function, 
        # or maybe we should default to None? 
        # "results show the tree open to the level 2 similar to the TUI version."
        # The user requested this behavior for CLI --simple. Reasonable to assume for API too.
        print_simple_tree(root_node, max_level=2)
        return

    tree = make_tree(root_node)

    return tree
