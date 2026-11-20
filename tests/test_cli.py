import pytest

from gatedmind import cli


def test_held_out_seed_is_refused_without_final():
    """Broken case: a build run peeks at seed 2 while it is still tuning."""
    for cmd in (["generate", "--seed", "2"], ["eval", "--seed", "2"], ["index", "--seed", "2"]):
        with pytest.raises(SystemExit) as e:
            cli.main(cmd)
        assert "held out" in str(e.value)


def test_ask_prints_an_answer(capsys, tmp_path, monkeypatch):
    monkeypatch.setenv("GATEDMIND_CACHE", str(tmp_path))
    assert (
        cli.main(
            ["ask", "--as", "p001", "--mode", "postfilter", "What is the audit date for Q1 2027?"]
        )
        == 0
    )
    assert "mode 2 (postfilter)" in capsys.readouterr().out


def test_tools_json(capsys):
    cli.main(["tools-json"])
    assert '"who_knows"' in capsys.readouterr().out
