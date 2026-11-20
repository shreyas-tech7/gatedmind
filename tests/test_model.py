from gatedmind import model


def test_quotes_with_citations_and_paraphrases_facts():
    ctx = [
        ("d001", "The atlas budget is $5. Owner is Ava."),
        ("d002", "Please keep this up to date."),
    ]
    out = model.answer("what is the atlas budget", ctx)
    lines = out.splitlines()
    assert lines[0] == "[d001] The atlas budget is $5."
    assert lines[-1] == "Summary: atlas budget: $5"
    assert model.cited(out) == ["d001", "d002"]


def test_nothing_without_context():
    assert model.answer("anything", []) == model.NOTHING
    assert model.cited(model.NOTHING) == []
