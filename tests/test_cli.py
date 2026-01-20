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
    
    # Expectation with icons (L0=Green Circle, L1=Yellow Circle)
    # Root (L0) -> ● Root
    # Group (L1) -> ○ Group 1
    # Child (L2) -> Child A (No icon, or depends on logic. Current logic: only L0/L1 get special icons)
    
    assert "- ● Root" in res
    assert "- ○ Group 1" in res
    assert "- Child A" in res

def test_get_ad_tree_simple_api(capsys):
    from igrinsdr_helper.igrinsdr_tree import get_ad_tree, _get_ad_tree
    
    import igrinsdr_helper.igrinsdr_tree as tree_mod
    
    orig_func = tree_mod._get_ad_tree
    
    child = MyNode("'Child A'", [])
    group = MyNode("<b>Group 1</b>", [child])
    root = MyNode("'Root'", [group])
    
    tree_mod._get_ad_tree = lambda x: root
    
    try:
        # Call with simple=True
        res = tree_mod.get_ad_tree([], simple=True)
        assert res is None 
        
        captured = capsys.readouterr()
        assert "- ● Root" in captured.out
        assert "- ○ Group 1" in captured.out
        assert "- Child A" in captured.out
        
    finally:
        tree_mod._get_ad_tree = orig_func

def test_print_simple_tree_depth_limit(capsys):
    child = MyNode("'Child A'", []) 
    group = MyNode("<b>Group 1</b>", [child]) 
    root = MyNode("'Root'", [group]) 
    
    print_simple_tree(root, max_level=1)
    captured = capsys.readouterr()
    res = captured.out

    assert "- ● Root" in res
    assert "- ○ Group 1" in res
    assert "    - Child A" not in res
