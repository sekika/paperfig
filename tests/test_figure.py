"""Tests for the core logic in paperfig.figure."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from paperfig.figure import Fig, FigError


@pytest.fixture
def valid_json_file(tmp_path):
    """Create a temporary valid JSON specification file."""
    data = {
        "1": {"type": "simple_plot", "title": "Test Figure"},
        "2": {
            "type": "multi",
            "row": 1,
            "column": 2,
            "figures": {
                "2a": {"type": "simple_plot"},
                "2b": {"type": "simple_plot"}
            }
        }
    }
    p = tmp_path / "fig.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


@pytest.fixture
def fig_instance(valid_json_file, tmp_path):
    """Return a Fig instance initialized with a temporary directory."""
    fig = Fig(valid_json_file)
    fig.fig_dir = tmp_path / "output"
    return fig


def test_init_load_success(valid_json_file):
    """Test that Fig initializes and loads JSON correctly."""
    fig = Fig(valid_json_file)
    assert fig.json_filename == valid_json_file
    assert "1" in fig.list
    assert fig.list["1"]["type"] == "simple_plot"


def test_init_file_not_found(tmp_path):
    """Test that Fig raises FigError if JSON file does not exist."""
    non_existent = tmp_path / "missing.json"
    with pytest.raises(FigError, match="JSON file does not exist"):
        Fig(non_existent)


def test_validate_json_invalid_structure(tmp_path):
    """Test validation fails for non-dict root or invalid nodes."""
    # Case 1: Root is a list, not a dict
    p = tmp_path / "bad_root.json"
    p.write_text("[]", encoding="utf-8")
    with pytest.raises(FigError, match="Root of JSON must be an object"):
        Fig(p)

    # Case 2: Figure node is not a dict
    p2 = tmp_path / "bad_node.json"
    p2.write_text('{"1": "not a dict"}', encoding="utf-8")
    with pytest.raises(FigError, match="spec must be an object"):
        Fig(p2)

    # Case 3: Missing 'type'
    p3 = tmp_path / "missing_type.json"
    p3.write_text('{"1": {"title": "No type"}}', encoding="utf-8")
    with pytest.raises(FigError, match="must have a string 'type'"):
        Fig(p3)


def test_validate_multi_constraints(tmp_path):
    """Test validation specific to 'multi' type figures."""
    # Missing 'figures'
    p1 = tmp_path / "multi_no_figs.json"
    p1.write_text('{"1": {"type": "multi", "row": 1, "column": 1}}', encoding="utf-8")
    with pytest.raises(FigError, match="multi requires 'figures' object"):
        Fig(p1)

    # Missing 'row' or 'column'
    p2 = tmp_path / "multi_no_grid.json"
    p2.write_text('{"1": {"type": "multi", "figures": {}}}', encoding="utf-8")
    with pytest.raises(FigError, match="multi requires 'row'"):
        Fig(p2)


def test_register_and_resolve_renderer(fig_instance):
    """Test registering a custom renderer and resolving it."""
    def dummy_renderer(idx, data, v):
        return True

    # Register manually
    fig_instance.register("custom_type", dummy_renderer)
    resolved = fig_instance._resolve_renderer("custom_type")
    assert resolved is dummy_renderer

    # Test failure resolution
    assert fig_instance._resolve_renderer("non_existent") is None


def test_resolve_renderer_dynamic_import(fig_instance):
    """Test resolving a renderer via 'module:function' string."""
    # We mock importlib to simulate a successful import
    with patch("importlib.import_module") as mock_import:
        mock_mod = MagicMock()
        mock_func = MagicMock()
        mock_mod.my_func = mock_func
        mock_import.return_value = mock_mod

        resolved = fig_instance._resolve_renderer("my_module:my_func")
        
        mock_import.assert_called_with("my_module")
        assert resolved == mock_func


@patch("paperfig.figure.concat_pdf_pages")
def test_create_pdf_simple(mock_concat, fig_instance):
    """Test creating PDFs for simple figures (no multi)."""
    # Create a simplified JSON for this test
    p = fig_instance.json_filename
    p.write_text(json.dumps({"1": {"type": "simple"}}), encoding="utf-8")
    fig_instance.load_json()

    # Define a renderer that simulates creating the file
    def simple_renderer(idx, data, verbose):
        # Must create the file expected by Fig
        out_file = fig_instance.fig_dir / f"fig{idx}.pdf"
        out_file.parent.mkdir(exist_ok=True, parents=True)
        out_file.touch()
        return "result_data"

    fig_instance.register("simple", simple_renderer)
    
    # Ensure the final concatenated file is created by the mock
    def side_effect_concat(input_files, output_file, col, row):
        Path(output_file).touch()
    mock_concat.side_effect = side_effect_concat

    # Execute
    fig_instance.create_pdf()

    # Assertions
    assert (fig_instance.fig_dir / "fig1.pdf").exists()
    assert fig_instance.result["1"] == "result_data"
    
    # Verify concatenation was called
    expected_out = str(fig_instance.fig_dir / "figures.pdf")
    mock_concat.assert_called_once()
    args, kwargs = mock_concat.call_args
    assert kwargs["output_file"] == expected_out


@patch("paperfig.figure.concat_pdf_pages")
def test_create_pdf_multi(mock_concat, fig_instance):
    """Test recursively creating PDFs for multi-layout figures."""
    # The fixture already has a multi setup at key "2" with children "2a", "2b"
    
    def simple_renderer(idx, data, verbose):
        out_file = fig_instance.fig_dir / f"fig{idx}.pdf"
        out_file.parent.mkdir(exist_ok=True, parents=True)
        out_file.touch()
        return f"result_{idx}"

    fig_instance.register("simple_plot", simple_renderer)
    
    # Mock behavior: Create the output file when concat is called
    def side_effect_concat(input_files, output_file, col, row):
        Path(output_file).touch()
    
    mock_concat.side_effect = side_effect_concat
    
    # Execute
    fig_instance.create_pdf()

    # Check existence of sub-figures
    assert (fig_instance.fig_dir / "fig1.pdf").exists()
    assert (fig_instance.fig_dir / "fig2a.pdf").exists()
    assert (fig_instance.fig_dir / "fig2b.pdf").exists()
    
    # Check existence of combined figures (created by mock side effect)
    assert (fig_instance.fig_dir / "fig2.pdf").exists()
    assert (fig_instance.fig_dir / "figures.pdf").exists()


def test_renderer_output_missing(fig_instance):
    """Test error raised if renderer runs but fails to produce a PDF file."""
    p = fig_instance.json_filename
    p.write_text(json.dumps({"1": {"type": "ghost"}}), encoding="utf-8")
    fig_instance.load_json()

    # Renderer does nothing (does not create file)
    # Must accept 'verbose' as keyword argument
    fig_instance.register("ghost", lambda i, d, verbose=None: None)

    with pytest.raises(FigError, match="expected file not found"):
        fig_instance.create_pdf()


def test_save_json(fig_instance):
    """Test saving the JSON spec back to disk."""
    fig_instance.list["1"]["title"] = "Modified Title"
    fig_instance.save_json()
    
    with open(fig_instance.json_filename, "r") as f:
        data = json.load(f)
    assert data["1"]["title"] == "Modified Title"
