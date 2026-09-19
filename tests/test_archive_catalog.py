from core.archive_catalog import discover_collections, validate_collection

def collection():
    return {
        "id":"moh:collection:test","name":"Test Newspaper Archive","provider":"Example Library",
        "region":"Southern Africa","source_types":["newspaper","periodical"],
        "coverage":{"start":"1900","end":"1990"},"ocr_available":True,
        "bulk_data_available":False,"access":"mixed"
    }

def test_collection_validation():
    validate_collection(collection())

def test_discover_by_region_and_type():
    results = discover_collections([collection()], region="southern africa", source_type="newspaper")
    assert [item["id"] for item in results] == ["moh:collection:test"]

def test_access_filter():
    assert discover_collections([collection()], access={"open"}) == []

def test_invalid_collection_id():
    bad = collection()
    bad["id"] = "moh:bad"
    try:
        validate_collection(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected invalid collection id")
