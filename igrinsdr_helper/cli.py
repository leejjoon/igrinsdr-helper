import argparse
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Tree, Footer, Input
from textual.binding import Binding
from textual.containers import Container
from rich.text import Text
from igrinsdr_helper.igrinsdr_tree import _get_ad_tree

def convert_markup(label):
    """Convert simple HTML-like markup to Textual markup."""
    # Remove single quotes that might be around labels from the original helper
    label = label.strip("'")
    return label.replace("<b>", "[b]").replace("</b>", "[/b]")

class IgrinsTree(Tree):
    BINDINGS = [
        Binding("tab", "toggle_node", "Toggle Node"),
    ]

class IgrinsDrApp(App):
    CSS = """
    IgrinsTree {
        padding: 1;
        width: 100%;
        height: 1fr;
    }
    Input {
        dock: bottom;
        width: 100%;
        height: 3;
        display: none;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("/", "search", "Search"),
    ]

    def __init__(self, root_node, **kwargs):
        super().__init__(**kwargs)
        self.root_node_data = root_node
        self.original_labels = {} # Store original labels to restore after search

    def compose(self) -> ComposeResult:
        yield IgrinsTree("IGRINS DR Helper")
        yield Input(placeholder="Search...")
        yield Footer()

    def on_mount(self):
        tree = self.query_one(IgrinsTree)
        tree.show_root = False 
        self.build_tree(tree.root, self.root_node_data, level=1)
        tree.root.expand()

    def build_tree(self, tree_node, data_node, level=1):
        clean_curr_label = convert_markup(data_node.label)
        tree_node.label = clean_curr_label
        # Store for restoration (using id or object ref as key)
        self.original_labels[tree_node] = clean_curr_label

        if level < 3:
             tree_node.expand()

        for child in data_node.children:
            if not child.children:
                lbl = convert_markup(child.label)
                leaf = tree_node.add_leaf(lbl)
                self.original_labels[leaf] = lbl
            else:
                lbl = convert_markup(child.label)
                new_node = tree_node.add(lbl)
                self.original_labels[new_node] = lbl
                self.build_tree(new_node, child, level=level+1)

    def action_search(self):
        input_widget = self.query_one(Input)
        input_widget.display = True
        input_widget.focus()

    def on_input_submitted(self, message: Input.Submitted):
        query = message.value.lower()
        tree = self.query_one(IgrinsTree)
        
        # Reset labels
        for node, original in self.original_labels.items():
            node.label = original

        if query:
            self.highlight_nodes(tree.root, query)
        
        # Hide input and focus tree
        input_widget = self.query_one(Input)
        input_widget.display = False
        input_widget.value = ""
        tree.focus()

    def highlight_nodes(self, node, query):
        original_markup = self.original_labels.get(node, str(node.label))
        
        # We need to check if the PLAIN text matches the query to decide if we highlight
        # Textual/Rich can parse the markup to text.
        text_obj = Text.from_markup(original_markup)
        plain_text = text_obj.plain.lower()

        if query in plain_text:
            # Match found
            # 1. Highlight the matching word(s) with emphasized color (e.g., bold yellow or red)
            # 2. Highlight the background of the entire line (e.g., dark grey/blue)
            
            # Use Rich's highlight_regex/words
            # First, apply background to the whole text
            text_obj.stylize("on #2a2a2a") # Subtle background
            
            # Then highlight the query
            # Note: generic matching might be tricky if query is regex specials, assuming text query
            import re
            # Escape query just in case, and compile with ignore case
            escaped_query = re.escape(query)
            pattern = re.compile(escaped_query, re.IGNORECASE)
            text_obj.highlight_regex(pattern, "bold #ff00ff") # Emphasized text color (magenta/pink)

            node.label = text_obj
            node.expand()
            
            parent = node.parent
            while parent:
                 parent.expand()
                 parent = parent.parent

        for child in node.children:
            self.highlight_nodes(child, query)

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
