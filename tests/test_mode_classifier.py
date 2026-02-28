from app.services.mode_classifier import classify_mode_key
from app.services.queue_catalog import QueueCatalogItem

def test_classify_tft():
    item = QueueCatalogItem(queue_id=1090, map_name="Convergence", description="TFT Normal", notes=None)
    assert classify_mode_key(item) == "tft"

def test_classify_aram():
    item = QueueCatalogItem(queue_id=450, map_name="Howling Abyss", description="ARAM", notes=None)
    assert classify_mode_key(item) == "aram"

def test_classify_sr():
    item = QueueCatalogItem(queue_id=420, map_name="Summoner's Rift", description="Ranked Solo", notes=None)
    assert classify_mode_key(item) == "sr"

def test_classify_unkown_default_to_rotating():
    item = QueueCatalogItem(queue_id=9999, map_name="Some New Map", description="Mystery Mode", notes="???")
    assert classify_mode_key(item) == "rotating"