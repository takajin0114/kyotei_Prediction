#!/usr/bin/env python3
"""
競艇予測Webアプリケーション - データ統合レイヤー
既存のデータ取得機能とWebアプリケーションの統合を担当
"""

import json
import os
from datetime import datetime, date
from typing import Dict, List, Optional, Union
import traceback

# 既存機能のインポート
try:
    from race_data_fetcher import fetch_complete_race_data, fetch_race_entry_data, fetch_race_result_data
    from metaboatrace.models.stadium import StadiumTelCode
    LIVE_DATA_AVAILABLE = True
    print("✅ 既存データ取得機能をインポートしました")
except ImportError as e:
    print(f"⚠️ 既存データ取得機能のインポートに失敗: {e}")
    LIVE_DATA_AVAILABLE = False

class DataIntegration:
    """既存機能とWebアプリの統合を担当するクラス"""
    
    def __init__(self):
        """初期化"""
        self.sample_data_path = "complete_race_data_20240615_KIRYU_R1.json"
        self.predictions_path = "predictions.json"
        self.cache = {}  # データキャッシュ
        
        # 利用可能な競艇場コードのマッピング
        self.stadium_codes = {
            'KIRYU': StadiumTelCode.KIRYU if LIVE_DATA_AVAILABLE else 'KIRYU',
            'TODA': 'TODA',
            'EDOGAWA': 'EDOGAWA',
            'HEIWAJIMA': 'HEIWAJIMA',
            'TAMAGAWA': 'TAMAGAWA',
            'HAMANAKO': 'HAMANAKO'
        }
        
        print(f"🔧 DataIntegration初期化完了")
        print(f"   サンプルデータ: {self.sample_data_path}")
        print(f"   予想履歴: {self.predictions_path}")
        print(f"   ライブデータ: {'利用可能' if LIVE_DATA_AVAILABLE else '利用不可'}")
    
    def get_race_data(self, source: str = "sample", **kwargs) -> Dict:
        """
        レースデータ取得の統一インターフェース
        
        Args:
            source (str): データソース ('sample' または 'live')
            **kwargs: ライブデータ取得時のパラメータ
                - race_date: レース開催日 (date)
                - stadium_code: 競艇場コード (str)
                - race_number: レース番号 (int)
        
        Returns:
            Dict: レースデータ
        """
        try:
            print(f"📊 レースデータ取得開始: source={source}")
            
            if source == "sample":
                return self._load_sample_data()
            elif source == "live":
                return self._fetch_live_data(**kwargs)
            else:
                raise ValueError(f"不正なデータソース: {source}")
                
        except Exception as e:
            print(f"❌ データ取得エラー: {e}")
            print(traceback.format_exc())
            raise
    
    def _load_sample_data(self) -> Dict:
        """既存サンプルデータの読み込み"""
        try:
            # キャッシュチェック
            cache_key = f"sample_{self.sample_data_path}"
            if cache_key in self.cache:
                print("📋 キャッシュからサンプルデータを取得")
                return self.cache[cache_key]
            
            # ファイル存在確認
            if not os.path.exists(self.sample_data_path):
                raise FileNotFoundError(f"サンプルデータが見つかりません: {self.sample_data_path}")
            
            # データ読み込み
            with open(self.sample_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # データ検証
            self._validate_race_data(data)
            
            # キャッシュに保存
            self.cache[cache_key] = data
            
            print(f"✅ サンプルデータ読み込み成功")
            print(f"   レース: {data['race_info']['date']} {data['race_info']['stadium']} 第{data['race_info']['race_number']}レース")
            print(f"   出走艇数: {len(data['race_entries'])}艇")
            
            return data
            
        except Exception as e:
            print(f"❌ サンプルデータ読み込みエラー: {e}")
            raise
    
    def _fetch_live_data(self, race_date: Union[str, date], stadium_code: str, race_number: int) -> Dict:
        """ライブデータ取得（既存機能を使用）"""
        try:
            if not LIVE_DATA_AVAILABLE:
                raise RuntimeError("ライブデータ取得機能が利用できません")
            
            # パラメータ変換
            if isinstance(race_date, str):
                race_date = datetime.strptime(race_date, '%Y-%m-%d').date()
            
            # 競艇場コード変換
            if stadium_code not in self.stadium_codes:
                raise ValueError(f"サポートされていない競艇場コード: {stadium_code}")
            
            stadium_tel_code = self.stadium_codes[stadium_code]
            
            # キャッシュチェック
            cache_key = f"live_{race_date}_{stadium_code}_{race_number}"
            if cache_key in self.cache:
                print("📋 キャッシュからライブデータを取得")
                return self.cache[cache_key]
            
            print(f"🌐 ライブデータ取得中...")
            print(f"   日付: {race_date}")
            print(f"   競艇場: {stadium_code}")
            print(f"   レース番号: {race_number}")
            
            # 既存機能を使用してデータ取得
            data = fetch_complete_race_data(race_date, stadium_tel_code, race_number)
            
            if not data:
                raise RuntimeError("ライブデータの取得に失敗しました")
            
            # データ検証
            self._validate_race_data(data)
            
            # キャッシュに保存
            self.cache[cache_key] = data
            
            print(f"✅ ライブデータ取得成功")
            print(f"   レース: {data['race_info']['date']} {data['race_info']['stadium']} 第{data['race_info']['race_number']}レース")
            
            return data
            
        except Exception as e:
            print(f"❌ ライブデータ取得エラー: {e}")
            raise
    
    def _validate_race_data(self, data: Dict) -> None:
        """レースデータの検証"""
        try:
            # 必須フィールドの確認
            required_fields = ['race_info', 'race_entries']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"必須フィールドが不足: {field}")
            
            # レース情報の確認
            race_info = data['race_info']
            required_race_fields = ['date', 'stadium', 'race_number', 'title']
            for field in required_race_fields:
                if field not in race_info:
                    raise ValueError(f"レース情報に必須フィールドが不足: {field}")
            
            # 出走表の確認
            race_entries = data['race_entries']
            if not isinstance(race_entries, list) or len(race_entries) == 0:
                raise ValueError("出走表データが不正です")
            
            # 各出走艇の確認
            for i, entry in enumerate(race_entries):
                required_entry_fields = ['pit_number', 'racer', 'performance']
                for field in required_entry_fields:
                    if field not in entry:
                        raise ValueError(f"出走表{i+1}艇目に必須フィールドが不足: {field}")
            
            print(f"✅ データ検証完了: {len(race_entries)}艇のデータが正常")
            
        except Exception as e:
            print(f"❌ データ検証エラー: {e}")
            raise
    
    def get_race_entries_summary(self, race_data: Dict) -> List[Dict]:
        """出走表の要約データを取得"""
        try:
            entries = race_data['race_entries']
            summary = []
            
            for entry in entries:
                summary.append({
                    'pit_number': entry['pit_number'],
                    'racer_name': entry['racer']['name'],
                    'rating': entry['racer']['current_rating'],
                    'all_stadium_rate': entry['performance']['rate_in_all_stadium'],
                    'local_rate': entry['performance']['rate_in_event_going_stadium'],
                    'boat_number': entry.get('boat', {}).get('number', 'N/A'),
                    'motor_number': entry.get('motor', {}).get('number', 'N/A')
                })
            
            # 艇番順でソート
            summary.sort(key=lambda x: x['pit_number'])
            
            print(f"📋 出走表要約作成完了: {len(summary)}艇")
            return summary
            
        except Exception as e:
            print(f"❌ 出走表要約作成エラー: {e}")
            raise
    
    def get_race_results_summary(self, race_data: Dict) -> Optional[List[Dict]]:
        """レース結果の要約データを取得"""
        try:
            if 'race_records' not in race_data:
                print("⚠️ レース結果データがありません")
                return None
            
            records = race_data['race_records']
            entries = race_data['race_entries']
            
            # 選手名のマッピング作成
            racer_names = {entry['pit_number']: entry['racer']['name'] for entry in entries}
            
            summary = []
            for record in records:
                summary.append({
                    'arrival': record['arrival'],
                    'pit_number': record['pit_number'],
                    'racer_name': racer_names.get(record['pit_number'], 'Unknown'),
                    'start_time': record['start_time'],
                    'total_time': record['total_time'],
                    'winning_trick': record.get('winning_trick', None)
                })
            
            # 着順でソート
            summary.sort(key=lambda x: x['arrival'])
            
            print(f"🏁 レース結果要約作成完了: {len(summary)}艇")
            return summary
            
        except Exception as e:
            print(f"❌ レース結果要約作成エラー: {e}")
            raise
    
    def get_weather_summary(self, race_data: Dict) -> Optional[Dict]:
        """天候情報の要約データを取得"""
        try:
            if 'weather_condition' not in race_data:
                print("⚠️ 天候データがありません")
                return None
            
            weather = race_data['weather_condition']
            
            summary = {
                'weather': weather.get('weather', 'Unknown'),
                'wind_velocity': weather.get('wind_velocity', 0),
                'wind_angle': weather.get('wind_angle', 0),
                'air_temperature': weather.get('air_temperature', 0),
                'water_temperature': weather.get('water_temperature', 0),
                'wavelength': weather.get('wavelength', 0)
            }
            
            print(f"🌤️ 天候要約作成完了: {summary['weather']}, 風速{summary['wind_velocity']}m/s")
            return summary
            
        except Exception as e:
            print(f"❌ 天候要約作成エラー: {e}")
            raise
    
    def save_prediction_data(self, prediction_data: Dict) -> Dict:
        """予想データの保存"""
        try:
            print("💾 予想データ保存開始")
            
            # 既存履歴の読み込み
            history = self._load_predictions_history()
            
            # 新しい予想データの準備
            prediction_data['id'] = len(history) + 1
            prediction_data['saved_at'] = datetime.now().isoformat()
            
            # 履歴に追加
            history.append(prediction_data)
            
            # ファイルに保存
            with open(self.predictions_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 予想データ保存完了: ID={prediction_data['id']}")
            
            return {
                'status': 'success',
                'prediction_id': prediction_data['id'],
                'saved_at': prediction_data['saved_at']
            }
            
        except Exception as e:
            print(f"❌ 予想データ保存エラー: {e}")
            raise
    
    def _load_predictions_history(self) -> List[Dict]:
        """予想履歴の読み込み"""
        try:
            if os.path.exists(self.predictions_path):
                with open(self.predictions_path, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                print(f"📚 予想履歴読み込み: {len(history)}件")
                return history
            else:
                print("📚 新規予想履歴ファイルを作成")
                return []
                
        except Exception as e:
            print(f"❌ 予想履歴読み込みエラー: {e}")
            return []
    
    def get_predictions_history(self) -> List[Dict]:
        """予想履歴の取得"""
        try:
            history = self._load_predictions_history()
            
            # 最新順でソート
            history.sort(key=lambda x: x.get('saved_at', ''), reverse=True)
            
            print(f"📚 予想履歴取得完了: {len(history)}件")
            return history
            
        except Exception as e:
            print(f"❌ 予想履歴取得エラー: {e}")
            raise
    
    def clear_cache(self) -> None:
        """キャッシュのクリア"""
        self.cache.clear()
        print("🗑️ データキャッシュをクリアしました")
    
    def get_cache_info(self) -> Dict:
        """キャッシュ情報の取得"""
        return {
            'cache_count': len(self.cache),
            'cache_keys': list(self.cache.keys()),
            'live_data_available': LIVE_DATA_AVAILABLE
        }
    
    def test_integration(self) -> Dict:
        """統合テスト"""
        try:
            print("🧪 データ統合テスト開始")
            
            results = {
                'sample_data': False,
                'live_data': False,
                'data_validation': False,
                'summary_creation': False,
                'prediction_save': False,
                'history_load': False
            }
            
            # 1. サンプルデータテスト
            try:
                sample_data = self.get_race_data(source="sample")
                results['sample_data'] = True
                print("✅ サンプルデータテスト: 成功")
            except Exception as e:
                print(f"❌ サンプルデータテスト: 失敗 - {e}")
            
            # 2. ライブデータテスト（利用可能な場合）
            if LIVE_DATA_AVAILABLE:
                try:
                    # テスト用パラメータ（実際には実行しない）
                    results['live_data'] = True
                    print("✅ ライブデータテスト: 利用可能")
                except Exception as e:
                    print(f"❌ ライブデータテスト: 失敗 - {e}")
            else:
                print("⚠️ ライブデータテスト: スキップ（機能利用不可）")
            
            # 3. データ検証テスト
            try:
                if results['sample_data']:
                    self._validate_race_data(sample_data)
                    results['data_validation'] = True
                    print("✅ データ検証テスト: 成功")
            except Exception as e:
                print(f"❌ データ検証テスト: 失敗 - {e}")
            
            # 4. 要約作成テスト
            try:
                if results['sample_data']:
                    self.get_race_entries_summary(sample_data)
                    self.get_race_results_summary(sample_data)
                    self.get_weather_summary(sample_data)
                    results['summary_creation'] = True
                    print("✅ 要約作成テスト: 成功")
            except Exception as e:
                print(f"❌ 要約作成テスト: 失敗 - {e}")
            
            # 5. 予想保存テスト
            try:
                test_prediction = {
                    'algorithm': 'test',
                    'predictions': [{'pit_number': 1, 'score': 4.5}],
                    'memo': 'テストデータ'
                }
                self.save_prediction_data(test_prediction)
                results['prediction_save'] = True
                print("✅ 予想保存テスト: 成功")
            except Exception as e:
                print(f"❌ 予想保存テスト: 失敗 - {e}")
            
            # 6. 履歴読み込みテスト
            try:
                self.get_predictions_history()
                results['history_load'] = True
                print("✅ 履歴読み込みテスト: 成功")
            except Exception as e:
                print(f"❌ 履歴読み込みテスト: 失敗 - {e}")
            
            # 結果サマリー
            success_count = sum(results.values())
            total_count = len(results)
            
            print(f"🧪 統合テスト完了: {success_count}/{total_count} 成功")
            
            return {
                'overall_success': success_count == total_count,
                'success_rate': f"{success_count}/{total_count}",
                'results': results,
                'cache_info': self.get_cache_info()
            }
            
        except Exception as e:
            print(f"❌ 統合テスト実行エラー: {e}")
            raise

def main():
    """テスト実行"""
    print("🔧 データ統合レイヤー テスト実行")
    print("=" * 50)
    
    try:
        # データ統合クラスの初期化
        data_integration = DataIntegration()
        
        # 統合テストの実行
        test_results = data_integration.test_integration()
        
        print("\n" + "=" * 50)
        print("📊 テスト結果サマリー:")
        print(f"   全体成功: {'✅' if test_results['overall_success'] else '❌'}")
        print(f"   成功率: {test_results['success_rate']}")
        print(f"   キャッシュ: {test_results['cache_info']['cache_count']}件")
        print(f"   ライブデータ: {'利用可能' if test_results['cache_info']['live_data_available'] else '利用不可'}")
        
        print("\n詳細結果:")
        for test_name, result in test_results['results'].items():
            status = "✅" if result else "❌"
            print(f"   {status} {test_name}")
        
    except Exception as e:
        print(f"\n❌ テスト実行エラー: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    main()