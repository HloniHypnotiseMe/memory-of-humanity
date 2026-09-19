from core.archive import create_archive_source, validate_archive_source


def test_newspaper_source():
    source = create_archive_source(
        "moh:source:bantu-world-1938-01",
        "Bantu World",
        "National Library of South Africa",
        date="1938-01",
        place="Johannesburg",
        language="English",
        access_status="open",
    )
    validate_archive_source(source)
    assert source["source_type"] == "newspaper"
    assert source["provenance"]["repository"] == "National Library of South Africa"


def test_invalid_source_id():
    try:
        validate_archive_source({
            "id": "moh:bad",
            "source_type": "newspaper",
            "title": "Example",
            "provenance": {"repository": "Archive"},
            "access": {"status": "open"},
        })
    except ValueError as exc:
        assert "moh:source:" in str(exc)
    else:
        raise AssertionError("expected invalid source id")


def test_access_status():
    source = create_archive_source("moh:source:x", "X", "Archive", access_status="subscription")
    assert source["access"]["status"] == "subscription"
