from crossword_agent.domain.parser import find_crossings, load_puzzle


def test_find_crossings_for_word_square():
    puzzle = load_puzzle("data/eval/mini_001.json")
    crossings = find_crossings(puzzle)
    assert len(crossings) == 9
    assert any(c.slot_a == "A1" and c.slot_b == "D1" and c.row == 0 and c.col == 0 for c in crossings)
