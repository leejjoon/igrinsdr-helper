import argparse
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Tree
from igrinsdr_helper.igrinsdr_tree import _get_ad_tree

def convert_markup(label):
    """Convert simple HTML-like markup to Textual markup."""
    # Remove single quotes that might be around labels from the original helper
    label = label.strip("'")
    return label.replace("<b>", "[b]").replace("</b>", "[/b]")

class IgrinsDrApp(App):
    CSS = """
    Tree {
        padding: 1;
    }
    """

    def __init__(self, root_node, **kwargs):
        super().__init__(**kwargs)
        self.root_node_data = root_node

    def compose(self) -> ComposeResult:
        yield Tree("IGRINS DR Helper")

    def on_mount(self):
        tree = self.query_one(Tree)
        tree.show_root = False # The root from logic is usually a container
        # Note: igrinsdr_tree._get_ad_tree returns a root node.
        # We can set the tree root label or just add children to it.
        # Let's inspect the root node label from _get_ad_tree.
        # It seems to be common tags.
        
        # Level 1 (Root) is handled by build_tree call, but since we are populating existing tree.root,
        # we treat tree.root as Level 1.
        self.build_tree(tree.root, self.root_node_data, level=1)
        tree.root.expand()

    def build_tree(self, tree_node, data_node, level=1):
        tree_node.label = convert_markup(data_node.label)
        if level < 3:
             tree_node.expand()

        for child in data_node.children:
            if not child.children:
                tree_node.add_leaf(convert_markup(child.label))
            else:
                new_node = tree_node.add(convert_markup(child.label))
                self.build_tree(new_node, child, level=level+1)

def print_simple_tree(node, level=0, max_level=None):
    indent = "  " * level
    # Strip markup for simple output
    clean_label = node.label.replace("<b>", "").replace("</b>", "").replace("'", "")
    print(f"{indent}- {clean_label}")
    
    if max_level is not None and level >= max_level:
        return

    for child in node.children:
        print_simple_tree(child, level + 1, max_level)

def main():
    parser = argparse.ArgumentParser(description="IGRINS DR Helper CLI")
    parser.add_argument("path", nargs="?", default=".", help="Input directory path")
    parser.add_argument("-s", "--simple", action="store_true", help="Use simple output mode")
    parser.add_argument("--pattern", default="*.fits", help="File pattern to match (default: *.fits)")
    parser.add_argument("--depth", type=int, default=2, help="Depth to print in simple mode (default: 2)")
    args = parser.parse_args()

    path = Path(args.path)
    if path.is_file():
        # If user points to a single file, maybe just process that? 
        # But global logic usually expects multiple files.
        files = [path]
    elif path.is_dir():
        files = list(path.glob(args.pattern))
    else:
        print(f"Error: {path} is not a valid directory or file.")
        return

    if not files:
        print(f"No files matching '{args.pattern}' found in {path}")
        return

    try:
        root = _get_ad_tree(files)
    except Exception as e:
        print(f"Error building tree: {e}")
        return

    if args.simple:
        print_simple_tree(root, max_level=args.depth)
    else:
        app = IgrinsDrApp(root)
        app.run()

if __name__ == "__main__":
    main()
