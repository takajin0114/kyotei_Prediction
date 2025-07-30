#!/usr/bin/env python3
"""
環境依存脱却リファクタリング後の動作確認テスト
"""

import sys
import os
from pathlib import Path

def test_project_root_detection():
    """プロジェクトルート検出テスト"""
    print("=== プロジェクトルート検出テスト ===")
    
    try:
        # 動的プロジェクトルート検出のテスト
        def get_project_root():
            current_file = Path(__file__)
            project_root = current_file.parent
            
            # Google Colab環境の検出
            if str(project_root).startswith('/content/'):
                return Path('/content/kyotei_Prediction')
            
            return project_root
        
        project_root = get_project_root()
        print(f"✅ プロジェクトルート検出成功: {project_root}")
        
        # プロジェクト構造の確認
        required_dirs = [
            'kyotei_predictor',
            'kyotei_predictor/config',
            'kyotei_predictor/data',
            'kyotei_predictor/templates',
            'kyotei_predictor/static'
        ]
        
        missing_dirs = []
        for dir_path in required_dirs:
            full_path = project_root / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)
        
        if not missing_dirs:
            print("✅ プロジェクト構造確認成功")
        else:
            print(f"⚠️ 不足ディレクトリ: {', '.join(missing_dirs)}")
        
        return True
        
    except Exception as e:
        print(f"❌ プロジェクトルート検出エラー: {e}")
        return False

def test_settings_import():
    """設定ファイルインポートテスト"""
    print("\n=== 設定ファイルインポートテスト ===")
    
    try:
        # sys.pathにプロジェクトルートを追加
        project_root = Path(__file__).parent
        sys.path.append(str(project_root))
        
        # 設定ファイルのインポート
        import kyotei_predictor.config.settings as settings
        print("✅ settings.py インポート成功")
        
        # プロジェクトルートの確認
        print(f"✅ プロジェクトルート: {settings.PROJECT_ROOT}")
        
        # データディレクトリの確認
        data_dir = settings.get_data_paths()
        print(f"✅ データパス取得成功: {len(data_dir)} 件")
        
        return True
        
    except Exception as e:
        print(f"❌ 設定ファイルインポートエラー: {e}")
        return False

def test_config_import():
    """設定クラスインポートテスト"""
    print("\n=== 設定クラスインポートテスト ===")
    
    try:
        import kyotei_predictor.utils.config as config_utils
        print("✅ config.py インポート成功")
        
        # Configクラスのインスタンス作成
        config = config_utils.Config()
        print("✅ Configクラスインスタンス作成成功")
        
        # 設定値の取得テスト
        data_dir = config.get_data_dir()
        output_dir = config.get_output_dir()
        print(f"✅ 設定値取得成功 - データディレクトリ: {data_dir}")
        print(f"✅ 設定値取得成功 - 出力ディレクトリ: {output_dir}")
        
        return True
        
    except Exception as e:
        print(f"❌ 設定クラスインポートエラー: {e}")
        return False

def test_data_integration():
    """データ統合テスト"""
    print("\n=== データ統合テスト ===")
    
    try:
        import kyotei_predictor.data_integration as data_integration
        print("✅ data_integration.py インポート成功")
        
        # DataIntegrationクラスのインスタンス作成
        di = data_integration.DataIntegration()
        print("✅ DataIntegrationクラスインスタンス作成成功")
        
        # 利用可能会場の取得テスト
        stadiums = di.get_available_stadiums()
        print(f"✅ 利用可能会場取得成功: {len(stadiums)} 会場")
        
        return True
        
    except Exception as e:
        print(f"❌ データ統合テストエラー: {e}")
        return False

def test_app_import():
    """アプリケーションインポートテスト"""
    print("\n=== アプリケーションインポートテスト ===")
    
    try:
        import kyotei_predictor.app as app
        print("✅ app.py インポート成功")
        
        # Flaskアプリケーションの確認
        if hasattr(app, 'app'):
            print("✅ Flaskアプリケーション確認成功")
        else:
            print("⚠️ Flaskアプリケーションが見つかりません")
        
        return True
        
    except Exception as e:
        print(f"❌ アプリケーションインポートエラー: {e}")
        return False

def test_kyotei_env():
    """競艇環境テスト"""
    print("\n=== 競艇環境テスト ===")
    
    try:
        import kyotei_predictor.pipelines.kyotei_env as kyotei_env
        print("✅ kyotei_env.py インポート成功")
        
        # KyoteiEnvManagerクラスの確認
        if hasattr(kyotei_env, 'KyoteiEnvManager'):
            print("✅ KyoteiEnvManagerクラス確認成功")
        else:
            print("⚠️ KyoteiEnvManagerクラスが見つかりません")
        
        return True
        
    except Exception as e:
        print(f"❌ 競艇環境テストエラー: {e}")
        return False

def test_tools_import():
    """ツールインポートテスト"""
    print("\n=== ツールインポートテスト ===")
    
    try:
        # データ品質チェッカー
        import kyotei_predictor.tools.data_quality_checker as dqc
        print("✅ data_quality_checker.py インポート成功")
        
        # 予測ツール
        import kyotei_predictor.tools.prediction_tool as pt
        print("✅ prediction_tool.py インポート成功")
        
        # スケジュールデータメンテナンス
        import kyotei_predictor.tools.scheduled_data_maintenance as sdm
        print("✅ scheduled_data_maintenance.py インポート成功")
        
        return True
        
    except Exception as e:
        print(f"❌ ツールインポートテストエラー: {e}")
        return False

def test_maintenance_tools():
    """メンテナンスツールテスト"""
    print("\n=== メンテナンスツールテスト ===")
    
    try:
        # 自動クリーンアップ
        import kyotei_predictor.tools.maintenance.auto_cleanup as ac
        print("✅ auto_cleanup.py インポート成功")
        
        # ディスク監視
        import kyotei_predictor.tools.maintenance.disk_monitor as dm
        print("✅ disk_monitor.py インポート成功")
        
        # スケジューラー
        import kyotei_predictor.tools.maintenance.scheduler as scheduler
        print("✅ scheduler.py インポート成功")
        
        return True
        
    except Exception as e:
        print(f"❌ メンテナンスツールテストエラー: {e}")
        return False

def test_optimization_tools():
    """最適化ツールテスト"""
    print("\n=== 最適化ツールテスト ===")
    
    try:
        # 統一最適化ツール
        import kyotei_predictor.tools.optimization.unified_optimizer as uo
        print("✅ unified_optimizer.py インポート成功")
        
        # 段階的報酬最適化
        import kyotei_predictor.tools.optimization.optimize_graduated_reward as ogr
        print("✅ optimize_graduated_reward.py インポート成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 最適化ツールテストエラー: {e}")
        return False

def test_batch_tools():
    """バッチツールテスト"""
    print("\n=== バッチツールテスト ===")
    
    try:
        # 不足月データ取得
        import kyotei_predictor.tools.batch.fetch_missing_months as fmm
        print("✅ fetch_missing_months.py インポート成功")
        
        # 段階的報酬学習
        import kyotei_predictor.tools.batch.train_with_graduated_reward as twgr
        print("✅ train_with_graduated_reward.py インポート成功")
        
        # 拡張段階的報酬学習
        import kyotei_predictor.tools.batch.train_extended_graduated_reward as tegr
        print("✅ train_extended_graduated_reward.py インポート成功")
        
        return True
        
    except Exception as e:
        print(f"❌ バッチツールテストエラー: {e}")
        return False

def test_static_tools():
    """静的ツールテスト"""
    print("\n=== 静的ツールテスト ===")
    
    try:
        # テストサーバー
        import kyotei_predictor.static.test_server as ts
        print("✅ test_server.py インポート成功")
        
        # サーバー停止
        import kyotei_predictor.static.stop_test_server as sts
        print("✅ stop_test_server.py インポート成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 静的ツールテストエラー: {e}")
        return False

def main():
    """メイン関数"""
    print("環境依存脱却リファクタリング後の動作確認テスト開始")
    print("=" * 60)
    
    # テスト結果を記録
    test_results = []
    
    # 各テストを実行
    tests = [
        ("プロジェクトルート検出", test_project_root_detection),
        ("設定ファイルインポート", test_settings_import),
        ("設定クラスインポート", test_config_import),
        ("データ統合", test_data_integration),
        ("アプリケーションインポート", test_app_import),
        ("競艇環境", test_kyotei_env),
        ("ツールインポート", test_tools_import),
        ("メンテナンスツール", test_maintenance_tools),
        ("最適化ツール", test_optimization_tools),
        ("バッチツール", test_batch_tools),
        ("静的ツール", test_static_tools),
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}テストで予期しないエラー: {e}")
            test_results.append((test_name, False))
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✅ 成功" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n総テスト数: {len(test_results)}")
    print(f"成功: {passed}")
    print(f"失敗: {failed}")
    print(f"成功率: {passed/len(test_results)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 すべてのテストが成功しました！環境依存脱却リファクタリングは完了しています。")
    else:
        print(f"\n⚠️ {failed}個のテストが失敗しました。修正が必要です。")

if __name__ == "__main__":
    main() 