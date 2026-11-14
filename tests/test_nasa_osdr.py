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


def test_redirect_to_nasa_subdomain_is_allowed_but_not_for_api_calls():
    assert nasa_osdr._host_allowed("osdr.nasa.gov")
    assert nasa_osdr._host_allowed("files.nasa.gov", redirect=True)
    assert not nasa_osdr._host_allowed("files.nasa.gov")
    assert not nasa_osdr._host_allowed("evil-nasa.gov", redirect=True)
    assert not nasa_osdr._host_allowed("nasa.gov.evil.com", redirect=True)
    assert not nasa_osdr._host_allowed(None)


def test_redirect_to_foreign_host_is_refused_before_following():
    handler = nasa_osdr._SafeRedirect()
    with pytest.raises(nasa_osdr.OSDRError):
        handler.redirect_request(None, None, 302, "Found", {}, "https://example.com/x.csv")
    with pytest.raises(nasa_osdr.OSDRError):
        handler.redirect_request(None, None, 302, "Found", {}, "http://osdr.nasa.gov/x.csv")


def test_study_files_falls_back_to_second_url_and_skips_foreign_links(monkeypatch):
    calls = []

    def fake_get_json(url):
        calls.append(url)
        if "/files/575/?" in url:
            raise nasa_osdr.OSDRError("HTTP 404")
        return {"575": {"files": [
            {"file_name": "a.csv", "remote_url": "/osdr/data/a.csv", "file_size": 10},
            {"file_name": "b.csv", "remote_url": "https://example.com/b.csv"},
        ]}}

    monkeypatch.setattr(nasa_osdr, "_get_json", fake_get_json)
    files = nasa_osdr.study_files("OSD-575")

    assert len(calls) == 2
    assert [f["name"] for f in files] == ["a.csv"]
    assert files[0]["download_url"] == "https://osdr.nasa.gov/osdr/data/a.csv"


def test_study_files_raises_last_error_when_every_url_fails(monkeypatch):
    def boom(url):
        raise nasa_osdr.OSDRError("HTTP 403")
    monkeypatch.setattr(nasa_osdr, "_get_json", boom)
    with pytest.raises(nasa_osdr.OSDRError, match="403"):
        nasa_osdr.study_files(575)


def test_table_members_rejects_path_traversal_and_big_files():
    import io
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("ok.csv", "a,b\n1,2\n")
        z.writestr("../evil.csv", "a\n1\n")
        z.writestr("sub/ok2.tsv", "a\tb\n1\t2\n")
        z.writestr("image.png", "x")
    with zipfile.ZipFile(io.BytesIO(buf.getvalue())) as z:
        assert sorted(nasa_osdr._table_members(z)) == ["ok.csv", "sub/ok2.tsv"]


def test_diagnose_reports_invalid_id_without_raising():
    result = nasa_osdr.diagnose("abc")
    assert result and result[0][1] is False
