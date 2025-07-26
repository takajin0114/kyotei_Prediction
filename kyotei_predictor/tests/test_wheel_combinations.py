#!/usr/bin/env python3
"""
Test for wheel pattern combinations calculation
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from kyotei_predictor.tools.prediction_tool import PredictionTool
import json

def test_wheel_combinations():
    """Test wheel pattern combinations calculation"""
    print("🧪 Testing wheel pattern combinations calculation...")
    
    # Create a mock top 20 combinations
    mock_combinations = [
        {'combination': '1-2-3', 'probability': 0.15, 'expected_value': 2.0, 'rank': 1},
        {'combination': '1-3-2', 'probability': 0.12, 'expected_value': 1.8, 'rank': 2},
        {'combination': '1-2-4', 'probability': 0.10, 'expected_value': 1.6, 'rank': 3},
        {'combination': '1-3-5', 'probability': 0.08, 'expected_value': 1.4, 'rank': 4},
        {'combination': '1-4-2', 'probability': 0.07, 'expected_value': 1.2, 'rank': 5},
        {'combination': '1-5-3', 'probability': 0.06, 'expected_value': 1.0, 'rank': 6},
        {'combination': '1-6-2', 'probability': 0.05, 'expected_value': 0.8, 'rank': 7},
        {'combination': '1-4-5', 'probability': 0.04, 'expected_value': 0.6, 'rank': 8},
        {'combination': '1-5-6', 'probability': 0.03, 'expected_value': 0.4, 'rank': 9},
        {'combination': '2-1-3', 'probability': 0.09, 'expected_value': 1.5, 'rank': 10},
        {'combination': '2-3-1', 'probability': 0.08, 'expected_value': 1.3, 'rank': 11},
        {'combination': '2-1-4', 'probability': 0.07, 'expected_value': 1.1, 'rank': 12},
        {'combination': '2-4-1', 'probability': 0.06, 'expected_value': 0.9, 'rank': 13},
        {'combination': '2-5-1', 'probability': 0.05, 'expected_value': 0.7, 'rank': 14},
        {'combination': '2-6-1', 'probability': 0.04, 'expected_value': 0.5, 'rank': 15},
        {'combination': '3-1-2', 'probability': 0.08, 'expected_value': 1.4, 'rank': 16},
        {'combination': '3-2-1', 'probability': 0.07, 'expected_value': 1.2, 'rank': 17},
        {'combination': '3-1-4', 'probability': 0.06, 'expected_value': 1.0, 'rank': 18},
        {'combination': '3-4-1', 'probability': 0.05, 'expected_value': 0.8, 'rank': 19},
        {'combination': '3-5-1', 'probability': 0.04, 'expected_value': 0.6, 'rank': 20},
    ]
    
    # Create PredictionTool instance
    tool = PredictionTool()
    
    # Test wheel suggestions generation
    wheel_suggestions = tool.generate_wheel_suggestions(mock_combinations)
    
    print(f"\n📊 Wheel suggestions generated: {len(wheel_suggestions)}")
    
    # Find the 1-流し suggestion
    one_wheel_suggestion = None
    for suggestion in wheel_suggestions:
        if suggestion['description'] == '1-流し':
            one_wheel_suggestion = suggestion
            break
    
    if one_wheel_suggestion:
        print(f"\n🎯 1-流し suggestion found:")
        print(f"   Description: {one_wheel_suggestion['description']}")
        print(f"   Total cost: ¥{one_wheel_suggestion['total_cost']}")
        print(f"   Purchase count (total_cost/100): {one_wheel_suggestion['total_cost'] // 100}")
        print(f"   Combinations in top 20: {len(one_wheel_suggestion['combinations'])}")
        print(f"   Combinations list: {one_wheel_suggestion['combinations']}")
        print(f"   Total probability: {one_wheel_suggestion['total_probability']:.3f}")
        
        # Calculate expected combinations for 1-流し
        expected_combinations = []
        for second in range(1, 7):
            if second == 1:  # Skip if same as first place
                continue
            for third in range(1, 7):
                if third == 1 or third == second:  # Skip if same as first or second
                    continue
                expected_combinations.append(f"1-{second}-{third}")
        
        print(f"\n📋 Expected combinations for 1-流し (should be 20):")
        print(f"   Expected count: {len(expected_combinations)}")
        print(f"   Expected combinations: {expected_combinations}")
        
        # Check which combinations are missing from top 20
        missing_combinations = [c for c in expected_combinations if c not in one_wheel_suggestion['combinations']]
        print(f"\n❌ Missing combinations from top 20: {len(missing_combinations)}")
        print(f"   Missing: {missing_combinations}")
        
        # Verify the issue
        if one_wheel_suggestion['total_cost'] // 100 == 20 and len(one_wheel_suggestion['combinations']) < 20:
            print(f"\n✅ Issue confirmed: Purchase count shows 20 but only {len(one_wheel_suggestion['combinations'])} combinations are displayed")
            print(f"   This is because only combinations in the top 20 predictions are shown")
        else:
            print(f"\n❌ Unexpected result")
            
    else:
        print(f"\n❌ 1-流し suggestion not found")
    
    # Test all wheel suggestions
    print(f"\n📈 All wheel suggestions:")
    for i, suggestion in enumerate(wheel_suggestions, 1):
        purchase_count = suggestion['total_cost'] // 100
        displayed_count = len(suggestion['combinations'])
        print(f"   {i}. {suggestion['description']}: {purchase_count}組 (表示: {displayed_count}組)")
    
    print(f"\n✅ Wheel combinations test completed")

if __name__ == "__main__":
    test_wheel_combinations() 