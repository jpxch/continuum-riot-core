from app.models.asset import AssetType
from app.services.static_ingestion import AssetResult, summarize_results


def test_summarize_results_counts_single_new():
    results = [
        AssetResult(
            asset_type=AssetType.CHAMPION,
            filename="champion.json",
            status="new",
        )
    ]

    assert summarize_results(results) == {
        "total": 1,
        "new": 1,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
    }


def test_summarize_results_counts_mixed_statuses():
    results = [
        AssetResult(AssetType.CHAMPION, "champion.json", "new"),
        AssetResult(AssetType.ITEM, "item.json", "updated"),
        AssetResult(AssetType.RUNE, "runesReforged.json", "skipped"),
        AssetResult(AssetType.SUMMONER, "summoner.json", "failed", "boom"),
    ]

    assert summarize_results(results) == {
        "total": 4,
        "new": 1,
        "updated": 1,
        "skipped": 1,
        "failed": 1,
    }


def test_summarize_results_counts_empty_results():
    assert summarize_results([]) == {
        "total": 0,
        "new": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
    }
