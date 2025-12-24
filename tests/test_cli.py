"""Tests for the command line interface in paperfig.cli."""

import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from paperfig.cli import main, cmd_build, cmd_validate, cmd_list
from paperfig.figure import FigError


@pytest.fixture
def cli_json_file(tmp_path):
    """Create a temporary valid JSON file for CLI tests."""
    data = {
        "1": {"type": "test_type", "title": "A"},
        "2": {"type": "test_type", "title": "B"}
    }
    p = tmp_path / "cli.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


@patch("paperfig.cli.Fig")
def test_cmd_build(mock_fig_cls, cli_json_file):
    """Test the build command logic."""
    # Setup mock
    mock_instance = mock_fig_cls.return_value
    mock_instance.list = {}
    
    # Create args
    args = argparse.Namespace(
        json_file=cli_json_file,
        outdir="out",
        output="final.pdf",
        verbose=1
    )
    
    # Run
    ret = cmd_build(args)
    
    # Verify
    assert ret == 0
    mock_fig_cls.assert_called_with(cli_json_file)
    assert mock_instance.fig_dir == "out"
    assert mock_instance.pdf_filename == "final.pdf"
    assert mock_instance.verbose == 1
    mock_instance.create_pdf.assert_called_once()


@patch("paperfig.cli.Fig")
def test_cmd_build_error(mock_fig_cls, cli_json_file):
    """Test build command handles FigError gracefully."""
    mock_instance = mock_fig_cls.return_value
    mock_instance.create_pdf.side_effect = FigError("Build failed")
    
    args = argparse.Namespace(
        json_file=cli_json_file, outdir="out", output="f.pdf", verbose=1
    )
    
    ret = cmd_build(args)
    assert ret == 2  # CLI returns 2 on error


@patch("paperfig.cli.Fig")
def test_cmd_validate(mock_fig_cls, cli_json_file):
    """Test validate command."""
    args = argparse.Namespace(json_file=cli_json_file)
    
    # Success case
    ret = cmd_validate(args)
    assert ret == 0
    mock_fig_cls.assert_called_with(cli_json_file)
    
    # Failure case
    mock_fig_cls.side_effect = FigError("Invalid JSON")
    ret = cmd_validate(args)
    assert ret == 2


@patch("paperfig.cli.Fig")
def test_cmd_list(mock_fig_cls, cli_json_file, capsys):
    """Test list command prints keys and types."""
    mock_instance = mock_fig_cls.return_value
    # Mock the internal list of figures
    mock_instance.list = {
        "1": {"type": "sine"},
        "2": {"type": "scatter"}
    }
    
    args = argparse.Namespace(json_file=cli_json_file)
    ret = cmd_list(args)
    
    assert ret == 0
    captured = capsys.readouterr()
    assert "1\tsine" in captured.out
    assert "2\tscatter" in captured.out


def test_main_parser_integration(cli_json_file):
    """Integration test for argument parsing and routing."""
    # We patch the specific cmd functions to verify routing without running logic
    with patch("paperfig.cli.cmd_validate") as mock_val:
        mock_val.return_value = 0
        
        # Simulate CLI arguments
        argv = ["validate", str(cli_json_file)]
        
        # main() raises SystemExit(0) on success
        with pytest.raises(SystemExit) as exc:
            main(argv)
        
        assert exc.value.code == 0
        mock_val.assert_called_once()
        # Verify the Namespace passed to the function contains correct path
        call_args = mock_val.call_args[0][0]
        assert call_args.json_file == cli_json_file
