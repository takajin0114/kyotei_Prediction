#!/usr/bin/env python3
"""
統合会場マッピング機能
"""
from typing import Dict, List, Optional, Any

from metaboatrace.models.stadium import StadiumTelCode

# 全24会場の詳細マッピング
VENUE_MAPPING = {
    StadiumTelCode.KIRYU: {
        'code': '01',
        'name': 'KIRYU',
        'japanese_name': '桐生',
        'region': '関東',
        'prefecture': '群馬県',
        'address': '群馬県桐生市新里町新川',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.TODA: {
        'code': '02',
        'name': 'TODA',
        'japanese_name': '戸田',
        'region': '関東',
        'prefecture': '埼玉県',
        'address': '埼玉県戸田市新曽',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.EDOGAWA: {
        'code': '03',
        'name': 'EDOGAWA',
        'japanese_name': '江戸川',
        'region': '関東',
        'prefecture': '東京都',
        'address': '東京都江戸川区臨海町',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.HEIWAJIMA: {
        'code': '04',
        'name': 'HEIWAJIMA',
        'japanese_name': '平和島',
        'region': '関東',
        'prefecture': '東京都',
        'address': '東京都大田区平和島',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.TAMAGAWA: {
        'code': '05',
        'name': 'TAMAGAWA',
        'japanese_name': '多摩川',
        'region': '関東',
        'prefecture': '東京都',
        'address': '東京都大田区多摩川',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.HAMANAKO: {
        'code': '06',
        'name': 'HAMANAKO',
        'japanese_name': '浜名湖',
        'region': '中部',
        'prefecture': '静岡県',
        'address': '静岡県浜松市西区舞阪町',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.GAMAGORI: {
        'code': '07',
        'name': 'GAMAGORI',
        'japanese_name': '蒲郡',
        'region': '中部',
        'prefecture': '愛知県',
        'address': '愛知県蒲郡市竹島町',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.TOKONAME: {
        'code': '08',
        'name': 'TOKONAME',
        'japanese_name': '常滑',
        'region': '中部',
        'prefecture': '愛知県',
        'address': '愛知県常滑市新開町',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.TSU: {
        'code': '09',
        'name': 'TSU',
        'japanese_name': '津',
        'region': '中部',
        'prefecture': '三重県',
        'address': '三重県津市丸之内',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.MIKUNI: {
        'code': '10',
        'name': 'MIKUNI',
        'japanese_name': '三国',
        'region': '中部',
        'prefecture': '福井県',
        'address': '福井県坂井市三国町',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.BIWAKO: {
        'code': '11',
        'name': 'BIWAKO',
        'japanese_name': '琵琶湖',
        'region': '中部',
        'prefecture': '滋賀県',
        'address': '滋賀県大津市本丸町',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.WAKAMATSU: {
        'code': '12',
        'name': 'WAKAMATSU',
        'japanese_name': '若松',
        'region': '中部',
        'prefecture': '福島県',
        'address': '福島県会津若松市',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.ASHIYA: {
        'code': '13',
        'name': 'ASHIYA',
        'japanese_name': '芦屋',
        'region': '中部',
        'prefecture': '福岡県',
        'address': '福岡県芦屋町',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.SUMINOE: {
        'code': '14',
        'name': 'SUMINOE',
        'japanese_name': '住之江',
        'region': '関西',
        'prefecture': '大阪府',
        'address': '大阪府大阪市住之江区',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.AMAGASAKI: {
        'code': '15',
        'name': 'AMAGASAKI',
        'japanese_name': '尼崎',
        'region': '関西',
        'prefecture': '兵庫県',
        'address': '兵庫県尼崎市',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.NARUTO: {
        'code': '16',
        'name': 'NARUTO',
        'japanese_name': '鳴門',
        'region': '関西',
        'prefecture': '徳島県',
        'address': '徳島県鳴門市',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.MARUGAME: {
        'code': '17',
        'name': 'MARUGAME',
        'japanese_name': '丸亀',
        'region': '関西',
        'prefecture': '香川県',
        'address': '香川県丸亀市',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.KOJIMA: {
        'code': '18',
        'name': 'KOJIMA',
        'japanese_name': '児島',
        'region': '関西',
        'prefecture': '岡山県',
        'address': '岡山県倉敷市児島',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.MIYAJIMA: {
        'code': '19',
        'name': 'MIYAJIMA',
        'japanese_name': '宮島',
        'region': '関西',
        'prefecture': '広島県',
        'address': '広島県廿日市市',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.FUKUOKA: {
        'code': '20',
        'name': 'FUKUOKA',
        'japanese_name': '福岡',
        'region': '九州',
        'prefecture': '福岡県',
        'address': '福岡県福岡市',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.KARATSU: {
        'code': '21',
        'name': 'KARATSU',
        'japanese_name': '唐津',
        'region': '九州',
        'prefecture': '佐賀県',
        'address': '佐賀県唐津市',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.OMURA: {
        'code': '22',
        'name': 'OMURA',
        'japanese_name': '大村',
        'region': '九州',
        'prefecture': '長崎県',
        'address': '長崎県大村市',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    # StadiumTelCode.BEPPU: {
    #     'code': '23',
    #     'name': 'BEPPU',
    #     'japanese_name': '別府',
    #     'region': '九州',
    #     'prefecture': '大分県',
    #     'address': '大分県別府市',
    #     'opened': '1952年',
    #     'capacity': '約2,000人'
    # },
    # StadiumTelCode.YANAGAWA: {
    #     'code': '24',
    #     'name': 'YANAGAWA',
    #     'japanese_name': '柳川',
    #     'region': '九州',
    #     'prefecture': '福岡県',
    #     'address': '福岡県柳川市',
    #     'opened': '1952年',
    #     'capacity': '約2,000人'
    # }
}

class VenueMapper:
    """会場マッピング管理クラス"""
    
    @staticmethod
    def get_venue_name(stadium: StadiumTelCode) -> str:
        """会場名を取得"""
        venue_info = VENUE_MAPPING.get(stadium)
        return venue_info['japanese_name'] if venue_info else str(stadium)
    
    @staticmethod
    def get_venue_code(stadium: StadiumTelCode) -> str:
        """会場コードを取得"""
        venue_info = VENUE_MAPPING.get(stadium)
        return venue_info['code'] if venue_info else str(stadium)
    
    @staticmethod
    def get_venue_region(stadium: StadiumTelCode) -> str:
        """会場地域を取得"""
        venue_info = VENUE_MAPPING.get(stadium)
        return venue_info['region'] if venue_info else '不明'
    
    @staticmethod
    def get_all_stadiums() -> List[StadiumTelCode]:
        """全競艇場のリストを取得"""
        return list(VENUE_MAPPING.keys())
    
    @staticmethod
    def get_stadium_info(stadium: StadiumTelCode) -> Optional[Dict[str, Any]]:
        """会場詳細情報を取得"""
        return VENUE_MAPPING.get(stadium)
    
    @staticmethod
    def get_stadium_by_code(code: str) -> Optional[StadiumTelCode]:
        """コードから会場を取得"""
        for stadium, info in VENUE_MAPPING.items():
            if info['code'] == code:
                return stadium
        return None
    
    @staticmethod
    def get_stadiums_by_region(region: str) -> List[StadiumTelCode]:
        """地域別会場リストを取得"""
        return [
            stadium for stadium, info in VENUE_MAPPING.items()
            if info['region'] == region
        ]
    
    @staticmethod
    def print_venue_mapping():
        """会場マッピングを表示"""
        print("=== 競艇場マッピング ===")
        for stadium, info in VENUE_MAPPING.items():
            print(f"{info['code']}: {info['japanese_name']} ({info['region']})")

# 便利な関数のエイリアス
get_venue_name = VenueMapper.get_venue_name
get_venue_code = VenueMapper.get_venue_code
get_venue_region = VenueMapper.get_venue_region
get_all_stadiums = VenueMapper.get_all_stadiums
get_stadium_info = VenueMapper.get_stadium_info
get_stadium_by_code = VenueMapper.get_stadium_by_code
get_stadiums_by_region = VenueMapper.get_stadiums_by_region 