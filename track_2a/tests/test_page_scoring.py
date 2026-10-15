from src.page_scoring import (
    calculate_idf,
    score_page,
    score_pages,
    select_page_blocks,
    select_relevant_pages,
)


def test_exact_title_match_gets_highest_score():
    pages = ("Introduction to the vote.", "Federal Act on Climate Protection")
    scores = score_pages(pages, "Federal Act on Climate Protection")
    assert scores[1] == 100.0
    assert scores[1] > scores[0]

def test_unrelated_page_scores_zero():
    pages = ("Apples and oranges are fruits.",)
    idf = calculate_idf(pages)
    score = score_page( pages[0], "Federal Act on Climate Protection", idf,)
    assert score == 0.0

def test_matching_title_words_increase_score():
    pages = ("General introduction.","The federal climate protection act changes existing policy.",)
    scores = score_pages(pages, "Federal climate protection act")
    assert scores[1] > scores[0]

def test_select_page_blocks_expands_context():
    scores = [0, 0, 20, 8, 0, 0]
    blocks = select_page_blocks(scores,min_score=15, expand_score=5, context_pages=1, max_pages=15,)
    assert blocks == [(2, 5)]

def test_multiple_relevant_regions_are_selected():
    scores = [0, 20, 0, 0, 25, 0]
    blocks = select_page_blocks( scores, min_score=15, expand_score=5, context_pages=0,  max_pages=15,)
    assert blocks == [(2, 2), (5, 5)]

def test_falls_back_to_full_booklet_if_no_page_meets_threshold():
    scores = [0, 3, 8, 2]
    blocks = select_page_blocks(scores, min_score=15)
    assert blocks == [(1, 4)]

def test_empty_scores_return_no_blocks():
    assert select_page_blocks([]) == []

def test_max_pages_limits_selected_pages():
    scores = [100, 0, 90, 0, 80, 0, 70, 0]
    blocks = select_page_blocks( scores, min_score=15, expand_score=5, context_pages=0, max_pages=3,)
    selected = [page for start, end in blocks for page in range(start, end + 1)]
    assert len(selected) <= 3

def test_select_relevant_pages_returns_zero_based_indices():
    pages = ("General introduction.", "Federal Act on Climate Protection.",)
    selected, scores = select_relevant_pages(pages,"Federal Act on Climate Protection",)
    assert 1 in selected
    assert len(scores) == len(pages)
