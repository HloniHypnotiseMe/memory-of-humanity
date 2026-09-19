from core.source_links import create_source_link, validate_source_link

def test_source_link():
    link = create_source_link("moh:sourcelink:1", "moh:memory:1", "moh:source:paper", "supports", "curator:1", locator={"page":"4"})
    validate_source_link(link)
    assert link["locator"]["page"] == "4"

def test_invalid_source_id():
    try:
        validate_source_link({"id":"moh:sourcelink:1","record_id":"moh:memory:1","source_id":"moh:bad","link_type":"supports","provenance":{"created_by":"curator:1"}})
    except ValueError:
        pass
    else:
        raise AssertionError("expected invalid source id")
