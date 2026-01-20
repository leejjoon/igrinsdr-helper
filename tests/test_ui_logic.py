import sys
from unittest.mock import MagicMock
import pytest
from textual.widgets import Tree
from textual.app import App

# Mock dependencies
sys.modules["astrodata"] = MagicMock()
sys.modules["igrins_instruments"] = MagicMock()

from igrinsdr_helper.cli import IgrinsDrApp, convert_markup

@pytest.mark.asyncio
async def test_highlight_logic():
    # Setup a simple tree
    app = IgrinsDrApp(MagicMock())
    tree = Tree("Root")
    app.original_labels = {}
    
    # Add nodes manually
    node1 = tree.root.add("Item 1")
    app.original_labels[node1] = "Item 1"
    
    node2 = tree.root.add("Special Item")
    app.original_labels[node2] = "Special Item"
    
    node3 = node2.add("Deep Item")
    app.original_labels[node3] = "Deep Item"

    # Test highlighting
    # We call highlight_nodes directly
    app.highlight_nodes(tree.root, "special")

    # Check labels
    # Note: Textual converts markup to rich.text.Text. str(text) returns plain text.
    # We check if the label has the 'reverse' style.
    
    # Node 1 should be plain (or just original)
    assert str(node1.label) == "Item 1"
    # It might have no spans or different spans from reverse
    
    # Node 2 should have valid styles
    assert "Special Item" in str(node2.label)
    
    # Check styles in spans
    # background should be present on at least one span (or all)
    # query highlight should be present
    
    styles = [span.style for span in node2.label.spans]
    # We expect "on #2a2a2a" and "bold #ff00ff"
    
    assert any("on #2a2a2a" in str(s) for s in styles)
    assert any("bold #ff00ff" in str(s) for s in styles)
    
    # Check expansion
    assert node2.is_expanded
    
    # Search for "Deep"
    app.highlight_nodes(tree.root, "deep")
    styles3 = [span.style for span in node3.label.spans]
    assert any("bold #ff00ff" in str(s) for s in styles3)
