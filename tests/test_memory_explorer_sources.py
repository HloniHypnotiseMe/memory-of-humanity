from core.memory_explorer import explore
from core.archive import create_archive_source
from core.records import create_memory
from core.source_links import create_source_link

def test_explorer_returns_relevant_sources():
    memory = create_memory("moh:memory:1", "Johannesburg memory", "person:1", "remembered")
    source = create_archive_source("moh:source:paper", "Historic newspaper", "Archive", date="1946")
    link = create_source_link("moh:sourcelink:1", memory["id"], source["id"], "mentions", "curator:1")
    result = explore([memory], [], text="Johannesburg", sources=[source], source_links=[link])
    assert result["sources"][0]["id"] == source["id"]
    assert result["source_links"][0]["id"] == link["id"]

def test_explorer_ignores_unrelated_source_links():
    memory = create_memory("moh:memory:1", "Johannesburg memory", "person:1", "remembered")
    source = create_archive_source("moh:source:paper", "Historic newspaper", "Archive", date="1946")
    link = create_source_link("moh:sourcelink:1", "moh:other", source["id"], "mentions", "curator:1")
    result = explore([memory], [], text="Johannesburg", sources=[source], source_links=[link])
    assert result["source_links"] == []
