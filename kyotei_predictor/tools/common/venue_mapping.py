#!/usr/bin/env python3
"""
会場マッピング（utils の再エクスポート）

重複を避けるため、実体は kyotei_predictor.utils.venue_mapping に集約しています。
このモジュールは後方互換のため残しています。
"""
from kyotei_predictor.utils.venue_mapping import (
    VENUE_MAPPING,
    VenueMapper,
    get_venue_name,
    get_venue_code,
    get_venue_region,
    get_all_stadiums,
    get_stadium_info,
    get_stadium_by_code,
    get_stadiums_by_region,
    print_venue_mapping,
)

__all__ = [
    "VENUE_MAPPING",
    "VenueMapper",
    "get_venue_name",
    "get_venue_code",
    "get_venue_region",
    "get_all_stadiums",
    "get_stadium_info",
    "get_stadium_by_code",
    "get_stadiums_by_region",
    "print_venue_mapping",
]
