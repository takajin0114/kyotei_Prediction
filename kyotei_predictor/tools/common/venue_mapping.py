#!/usr/bin/env python3
"""
全24会場の詳細マッピング情報
"""
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
        'japanese_name': 'びわこ',
        'region': '関西',
        'prefecture': '滋賀県',
        'address': '滋賀県大津市浜大津',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.SUMINOE: {
        'code': '12',
        'name': 'SUMINOE',
        'japanese_name': '住之江',
        'region': '関西',
        'prefecture': '大阪府',
        'address': '大阪府大阪市住之江区',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.AMAGASAKI: {
        'code': '13',
        'name': 'AMAGASAKI',
        'japanese_name': '尼崎',
        'region': '関西',
        'prefecture': '兵庫県',
        'address': '兵庫県尼崎市西本町',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.NARUTO: {
        'code': '14',
        'name': 'NARUTO',
        'japanese_name': '鳴門',
        'region': '四国',
        'prefecture': '徳島県',
        'address': '徳島県鳴門市鳴門町',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.MARUGAME: {
        'code': '15',
        'name': 'MARUGAME',
        'japanese_name': '丸亀',
        'region': '四国',
        'prefecture': '香川県',
        'address': '香川県丸亀市浜町',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.KOJIMA: {
        'code': '16',
        'name': 'KOJIMA',
        'japanese_name': '児島',
        'region': '中国',
        'prefecture': '岡山県',
        'address': '岡山県倉敷市児島',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.MIYAJIMA: {
        'code': '17',
        'name': 'MIYAJIMA',
        'japanese_name': '宮島',
        'region': '中国',
        'prefecture': '広島県',
        'address': '広島県廿日市市宮島町',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.TOKUYAMA: {
        'code': '18',
        'name': 'TOKUYAMA',
        'japanese_name': '徳山',
        'region': '中国',
        'prefecture': '山口県',
        'address': '山口県周南市徳山',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.SHIMONOSEKI: {
        'code': '19',
        'name': 'SHIMONOSEKI',
        'japanese_name': '下関',
        'region': '中国',
        'prefecture': '山口県',
        'address': '山口県下関市彦島',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.WAKAMATSU: {
        'code': '20',
        'name': 'WAKAMATSU',
        'japanese_name': '若松',
        'region': '九州',
        'prefecture': '福岡県',
        'address': '福岡県北九州市若松区',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.ASHIYA: {
        'code': '21',
        'name': 'ASHIYA',
        'japanese_name': '芦屋',
        'region': '九州',
        'prefecture': '福岡県',
        'address': '福岡県芦屋町芦屋',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.FUKUOKA: {
        'code': '22',
        'name': 'FUKUOKA',
        'japanese_name': '福岡',
        'region': '九州',
        'prefecture': '福岡県',
        'address': '福岡県福岡市博多区',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.KARATSU: {
        'code': '23',
        'name': 'KARATSU',
        'japanese_name': '唐津',
        'region': '九州',
        'prefecture': '佐賀県',
        'address': '佐賀県唐津市東唐津',
        'opened': '1952年',
        'capacity': '約2,000人'
    },
    StadiumTelCode.OMURA: {
        'code': '24',
        'name': 'OMURA',
        'japanese_name': '大村',
        'region': '九州',
        'prefecture': '長崎県',
        'address': '長崎県大村市古町',
        'opened': '1952年',
        'capacity': '約2,000人'
    }
}

def get_all_stadiums():
    """全24会場のStadiumTelCodeを返す"""
    return list(VENUE_MAPPING.keys())

def get_stadium_info(stadium: StadiumTelCode):
    """指定会場の詳細情報を返す"""
    return VENUE_MAPPING.get(stadium, {})

def get_stadium_by_code(code: str):
    """会場コードからStadiumTelCodeを取得"""
    for stadium, info in VENUE_MAPPING.items():
        if info['code'] == code:
            return stadium
    return None

def get_stadiums_by_region(region: str):
    """地域別に会場を取得"""
    return [stadium for stadium, info in VENUE_MAPPING.items() if info['region'] == region]

def print_venue_mapping():
    """会場マッピング情報を表示"""
    print("=== 全24会場マッピング情報 ===")
    print(f"{'コード':<4} {'会場名':<12} {'日本語名':<8} {'地域':<6} {'都道府県':<8}")
    print("-" * 50)
    
    for stadium, info in VENUE_MAPPING.items():
        print(f"{info['code']:<4} {info['name']:<12} {info['japanese_name']:<8} {info['region']:<6} {info['prefecture']:<8}")
    
    print(f"\n総会場数: {len(VENUE_MAPPING)}")
    
    # 地域別集計
    regions = {}
    for info in VENUE_MAPPING.values():
        region = info['region']
        regions[region] = regions.get(region, 0) + 1
    
    print("\n地域別会場数:")
    for region, count in sorted(regions.items()):
        print(f"  {region}: {count}会場")

if __name__ == "__main__":
    print_venue_mapping() 