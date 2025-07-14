import subprocess
import json
import os
import re
from datetime import datetime
import pytest

def test_prediction_tool_output(tmp_path):
    """
    prediction_tool.pyをE2E実行し、outputs/predictions_YYYY-MM-DD.jsonの内容を検証
    """
    # テスト日付（直近のデータがある日付を指定）
    test_date = '2025-07-08'
    output_dir = tmp_path
    # コマンド実行
    cmd = [
        'python', '-m', 'kyotei_predictor.tools.prediction_tool',
        '--predict-date', test_date,
        '--output-dir', str(output_dir)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, f"prediction_tool.py failed: {result.stderr}"
    # 出力ファイル確認
    out_json = os.path.join(output_dir, f'predictions_{test_date}.json')
    assert os.path.exists(out_json), f"Output JSON not found: {out_json}"
    with open(out_json, encoding='utf-8') as f:
        data = json.load(f)
    # サマリー検証
    assert 'prediction_date' in data and data['prediction_date'] == test_date
    assert 'predictions' in data and isinstance(data['predictions'], list)
    # 各レースの上位20組・購入提案を検証
    for race in data['predictions']:
        assert 'top_20_combinations' in race
        assert len(race['top_20_combinations']) == 20
        for c in race['top_20_combinations']:
            assert 'combination' in c and re.match(r'^[1-6]-[1-6]-[1-6]$', c['combination'])
            assert 'probability' in c and 0 <= c['probability'] <= 1
            assert 'expected_value' in c
            assert 'rank' in c and 1 <= c['rank'] <= 20
        assert 'purchase_suggestions' in race
        for s in race['purchase_suggestions']:
            assert 'type' in s and 'description' in s
            assert 'combinations' in s and isinstance(s['combinations'], list)
            assert 'total_probability' in s
            assert 'total_cost' in s
            assert 'expected_return' in s
    # サマリー・モデル情報も検証
    assert 'model_info' in data
    assert 'execution_summary' in data
    assert 'venue_summaries' in data 