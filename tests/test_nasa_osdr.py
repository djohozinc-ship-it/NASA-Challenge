"""Tests unitaires du client NASA OSDR."""
import pytest

from src import nasa_osdr


def test_study_id_accepts_osd_prefix_and_numeric_id():
    assert nasa_osdr._study_id("OSD-575") == "575"
    assert nasa_osdr._study_id(575) == "575"


@pytest.mark.parametrize("value", ["", "OSD-", "575abc", "../575", "OSD-5/75"])
def test_study_id_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        nasa_osdr._study_id(value)


def test_tsv_preview_uses_real_tab_delimiter():
    frame = nasa_osdr._tabular_frame(
        b"participant\tday\theart_rate\nP01\t1\t72\nP01\t2\t75\n",
        "measurements.tsv",
    )

    assert list(frame.columns) == ["participant", "day", "heart_rate"]
    assert frame.shape == (2, 3)
    assert frame.iloc[0]["heart_rate"] == 72


def test_csv_preview_keeps_comma_delimiter():
    frame = nasa_osdr._tabular_frame(
        b"participant,day,heart_rate\nP01,1,72\n",
        "measurements.csv",
    )

    assert list(frame.columns) == ["participant", "day", "heart_rate"]
    assert frame.iloc[0]["heart_rate"] == 72


def test_download_url_rejects_external_host():
    with pytest.raises(nasa_osdr.OSDRError):
        nasa_osdr._absolute_download_url("https://example.com/data.csv")


def test_download_url_resolves_osdr_relative_path():
    assert nasa_osdr._absolute_download_url("/osdr/data/file.csv") == (
        "https://osdr.nasa.gov/osdr/data/file.csv"
    )


def test_file_records_finds_nested_remote_urls():
    payload = {
        "data": {
            "files": [
                {"file_name": "table.csv", "remote_url": "/files/table.csv"},
                {"file_name": "readme.txt"},
            ]
        }
    }

    records = list(nasa_osdr._file_records(payload))

    assert len(records) == 1
    assert records[0]["file_name"] == "table.csv"
