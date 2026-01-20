import sys
from unittest.mock import MagicMock

# Mock dependencies that might be missing in the build env
sys.modules["astrodata"] = MagicMock()
sys.modules["igrins_instruments"] = MagicMock()

import pytest
from igrinsdr_helper.cli import print_simple_tree, convert_markup
from igrinsdr_helper.igrinsdr_tree import MyNode

def test_convert_markup():
    assert convert_markup("<b>Title</b>") == "[b]Title[/b]"
    assert convert_markup("'Title'") == "Title"
    # Test valid combination if possible, though exact behavior depends on data
    assert convert_markup("Normal") == "Normal"

def test_print_simple_tree(capsys):
    child = MyNode("'Child A'", [])
    group = MyNode("<b>Group 1</b>", [child])
    root = MyNode("'Root'", [group])
    
    print_simple_tree(root, max_level=2)
    
    captured = capsys.readouterr()
    res = captured.out
    
    # Expectation for max_level=2:
    # - Root (0)
    #   - Group 1 (1)
    #     - Child A (2) -- Printed because 2 is not >= 2? Wait.
    # Logic: if max_level is not None and level >= max_level: return.
    # Level 0: Print. Recurse (1).
    # Level 1: Print. Recurse (2).
    # Level 2: Print. Return (2 >= 2).
    
    # So we see 0, 1, 2. (Level 2 nodes are visible).
    
    assert "- Root" in res
    assert "  - Group 1" in res
    assert "    - Child A" in res

def test_print_simple_tree_depth_limit(capsys):
    child = MyNode("'Child A'", []) # Level 2 relative to root
    group = MyNode("<b>Group 1</b>", [child]) # Level 1
    root = MyNode("'Root'", [group]) # Level 0

    # If we set max_level=1
    # Level 0: Print. Recurse.
    # Level 1: Print. Return (1 >= 1).
    # Child A (Level 2) should NOT be printed.

    print_simple_tree(root, max_level=1)
    captured = capsys.readouterr()
    res = captured.out

    assert "- Root" in res
    assert "  - Group 1" in res
    assert "    - Child A" not in res
