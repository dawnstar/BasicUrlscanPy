import os

from base import BaseUrlscan


def test_get_quotas() -> None:
    """
    Test the get_quotas method
    """
    api_key = os.getenv("URLSCAN_API_KEY")
    base_urlscan = BaseUrlscan(api_key=api_key)
    response = base_urlscan.get_quotas()
    assert response is not None
    assert response.status_code == 200
    assert response.json() is not None
    print(response.json())
    assert "source" in response.json()


def test_get_scan_countries() -> None:
    """
    Test the get_scan_countries method
    """
    api_key = os.getenv("URLSCAN_API_KEY")
    base_urlscan = BaseUrlscan(api_key=api_key)
    response = base_urlscan.get_scan_countries()
    assert response is not None
    assert response.status_code == 200
    assert response.json() is not None
    print(response.json())
    assert "countries" in response.json()
