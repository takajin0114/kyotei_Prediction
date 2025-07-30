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
from pathlib import Path

# プロジェクトルートを動的に取得
def get_project_root() -> Path:
    """プロジェクトルートを動的に検出"""
    current_file = Path(__file__)
    project_root = current_file.parent
    
    # Google Colab環境の検出
    if str(project_root).startswith('/content/'):
        return Path('/content/kyotei_Prediction')
    
    return project_root

PROJECT_ROOT = get_project_root()

# 既存機能のインポート
from kyotei_predictor.tools.fetch.race_data_fetcher import fetch_complete_race_data, fetch_race_entry_data, fetch_race_result_data
from metaboatrace.models.stadium import StadiumTelCode

class DataIntegration:
    """既存機能とWebアプリの統合を担当するクラス"""
    
    def __init__(self):
        """初期化"""
        self.sample_data_path = PROJECT_ROOT / 'data' / 'complete_race_data_20240615_KIRYU_R1.json'
        self.predictions_path = PROJECT_ROOT / 'data' / 'predictions.json'
        self.cache = {}  # データキャッシュ
        
        # 利用可能な競艇場コードのマッピング
        self.stadium_codes = {
            'KIRYU': StadiumTelCode.KIRYU,
            'TODA': StadiumTelCode.TODA,
            'EDOGAWA': StadiumTelCode.EDOGAWA,
            'HEIWAJIMA': StadiumTelCode.HEIWAJIMA,
            'TAMAGAWA': StadiumTelCode.TAMAGAWA,
            'HAMANAKO': StadiumTelCode.HAMANAKO
        }
        
        print(f"🔧 DataIntegration初期化完了")
        print(f"   サンプルデータ: {self.sample_data_path}")
        print(f"   予想履歴: {self.predictions_path}")
        print(f"   ライブデータ: 利用可能")
    
    def get_race_data(self, source: str = "sample", **kwargs) -> Dict:
        """
        レースデータを取得
        
        Args:
            source: データソース ("sample", "live", "file")
            **kwargs: 追加パラメータ
            
        Returns:
            レースデータの辞書
        """
        try:
            if source == "sample":
                return self._get_sample_data()
            elif source == "live" and True: # LIVE_DATA_AVAILABLE is removed, so always True
                return self._get_live_data(**kwargs)
            elif source == "file":
                file_path = kwargs.get('file_path')
                if file_path:
                    return self._get_file_data(file_path)
                else:
                    raise ValueError("file_pathが必要です")
            else:
                raise ValueError(f"サポートされていないデータソース: {source}")
        except Exception as e:
            print(f"❌ データ取得エラー: {e}")
            return {"error": str(e)}
    
    def _get_sample_data(self) -> Dict:
        """サンプルデータを取得"""
        try:
            if self.sample_data_path.exists():
                with open(self.sample_data_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {"error": "サンプルデータファイルが見つかりません"}
        except Exception as e:
            return {"error": f"サンプルデータ読み込みエラー: {e}"}
    
    def _get_live_data(self, **kwargs) -> Dict:
        """ライブデータを取得"""
        try:
            stadium = kwargs.get('stadium', 'KIRYU')
            date_str = kwargs.get('date', date.today().strftime('%Y-%m-%d'))
            
            # ライブデータ取得を試行
            race_data = fetch_complete_race_data(stadium, date_str)
            return race_data
        except Exception as e:
            print(f"⚠️ ライブデータ取得エラー: {e}")
            # エラー時はサンプルデータをフォールバック
            return self._get_sample_data()
    
    def _get_file_data(self, file_path: str) -> Dict:
        """ファイルからデータを取得"""
        try:
            full_path = PROJECT_ROOT / file_path
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {"error": f"ファイルが見つかりません: {file_path}"}
        except Exception as e:
            return {"error": f"ファイル読み込みエラー: {e}"}
    
    def save_prediction(self, prediction_data: Dict) -> bool:
        """
        予測結果を保存
        
        Args:
            prediction_data: 予測データ
            
        Returns:
            保存成功時True
        """
        try:
            # 予測履歴を読み込み
            predictions = []
            if self.predictions_path.exists():
                with open(self.predictions_path, 'r', encoding='utf-8') as f:
                    predictions = json.load(f)
            
            # 新しい予測を追加
            prediction_data['timestamp'] = datetime.now().isoformat()
            predictions.append(prediction_data)
            
            # 保存
            self.predictions_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.predictions_path, 'w', encoding='utf-8') as f:
                json.dump(predictions, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"❌ 予測保存エラー: {e}")
            return False
    
    def get_prediction_history(self, limit: int = 10) -> List[Dict]:
        """
        予測履歴を取得
        
        Args:
            limit: 取得件数
            
        Returns:
            予測履歴のリスト
        """
        try:
            if self.predictions_path.exists():
                with open(self.predictions_path, 'r', encoding='utf-8') as f:
                    predictions = json.load(f)
                return predictions[-limit:]  # 最新のlimit件
            else:
                return []
        except Exception as e:
            print(f"❌ 予測履歴取得エラー: {e}")
            return []
    
    def get_available_stadiums(self) -> List[str]:
        """利用可能な競艇場のリストを取得"""
        return list(self.stadium_codes.keys())
    
    def validate_stadium(self, stadium: str) -> bool:
        """競艇場コードの妥当性を検証"""
        return stadium in self.stadium_codes
    
    def get_stadium_code(self, stadium: str) -> Optional[str]:
        """競艇場コードを取得"""
        return self.stadium_codes.get(stadium)
    
    def clear_cache(self):
        """キャッシュをクリア"""
        self.cache.clear()
        print("✅ キャッシュをクリアしました")
    
    def get_status(self) -> Dict:
        """システムステータスを取得"""
        return {
            "live_data_available": True, # LIVE_DATA_AVAILABLE is removed, so always True
            "sample_data_exists": self.sample_data_path.exists(),
            "predictions_file_exists": self.predictions_path.exists(),
            "cache_size": len(self.cache),
            "available_stadiums": self.get_available_stadiums()
        }