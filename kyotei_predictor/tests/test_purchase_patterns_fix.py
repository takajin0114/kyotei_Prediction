#!/usr/bin/env python3
"""
Test for purchase patterns combinations fix
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from kyotei_predictor.tools.prediction_tool import PredictionTool
import json

def test_purchase_patterns_fix():
    """Test that all purchase patterns show correct combinations"""
    print("🧪 Testing purchase patterns combinations fix...")
    
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
    
    # Test all purchase suggestion types
    print(f"\n📊 Testing all purchase suggestion types...")
    
    # Test wheel suggestions
    wheel_suggestions = tool.generate_wheel_suggestions(mock_combinations)
    print(f"\n🎯 Wheel suggestions: {len(wheel_suggestions)}")
    for suggestion in wheel_suggestions:
        purchase_count = suggestion['total_cost'] // 100
        displayed_count = len(suggestion['combinations'])
        print(f"   {suggestion['description']}: {purchase_count}組 (表示: {displayed_count}組)")
        if purchase_count != displayed_count:
            print(f"     ❌ MISMATCH: Expected {purchase_count}, got {displayed_count}")
        else:
            print(f"     ✅ CORRECT")
    
    # Test nagashi suggestions
    nagashi_suggestions = tool.generate_nagashi_suggestions(mock_combinations)
    print(f"\n🎯 Nagashi suggestions: {len(nagashi_suggestions)}")
    for suggestion in nagashi_suggestions:
        purchase_count = suggestion['total_cost'] // 100
        displayed_count = len(suggestion['combinations'])
        print(f"   {suggestion['description']}: {purchase_count}組 (表示: {displayed_count}組)")
        if purchase_count != displayed_count:
            print(f"     ❌ MISMATCH: Expected {purchase_count}, got {displayed_count}")
        else:
            print(f"     ✅ CORRECT")
    
    # Test box suggestions
    box_suggestions = tool.generate_box_suggestions(mock_combinations)
    print(f"\n🎯 Box suggestions: {len(box_suggestions)}")
    for suggestion in box_suggestions:
        purchase_count = suggestion['total_cost'] // 100
        displayed_count = len(suggestion['combinations'])
        print(f"   {suggestion['description']}: {purchase_count}組 (表示: {displayed_count}組)")
        if purchase_count != displayed_count:
            print(f"     ❌ MISMATCH: Expected {purchase_count}, got {displayed_count}")
        else:
            print(f"     ✅ CORRECT")
    
    # Test formation suggestions
    formation_suggestions = tool.generate_formation_suggestions(mock_combinations)
    print(f"\n🎯 Formation suggestions: {len(formation_suggestions)}")
    for suggestion in formation_suggestions:
        purchase_count = suggestion['total_cost'] // 100
        displayed_count = len(suggestion['combinations'])
        print(f"   {suggestion['description']}: {purchase_count}組 (表示: {displayed_count}組)")
        if purchase_count != displayed_count:
            print(f"     ❌ MISMATCH: Expected {purchase_count}, got {displayed_count}")
        else:
            print(f"     ✅ CORRECT")
    
    # Test complex wheel suggestions
    complex_wheel_suggestions = tool.generate_complex_wheel_suggestions(mock_combinations)
    print(f"\n🎯 Complex wheel suggestions: {len(complex_wheel_suggestions)}")
    for suggestion in complex_wheel_suggestions:
        purchase_count = suggestion['total_cost'] // 100
        displayed_count = len(suggestion['combinations'])
        print(f"   {suggestion['description']}: {purchase_count}組 (表示: {displayed_count}組)")
        if purchase_count != displayed_count:
            print(f"     ❌ MISMATCH: Expected {purchase_count}, got {displayed_count}")
        else:
            print(f"     ✅ CORRECT")
    
    # Test advanced formation suggestions
    advanced_formation_suggestions = tool.generate_advanced_formation_suggestions(mock_combinations)
    print(f"\n🎯 Advanced formation suggestions: {len(advanced_formation_suggestions)}")
    for suggestion in advanced_formation_suggestions:
        purchase_count = suggestion['total_cost'] // 100
        displayed_count = len(suggestion['combinations'])
        print(f"   {suggestion['description']}: {purchase_count}組 (表示: {displayed_count}組)")
        if purchase_count != displayed_count:
            print(f"     ❌ MISMATCH: Expected {purchase_count}, got {displayed_count}")
        else:
            print(f"     ✅ CORRECT")
    
    # Test all purchase suggestions together
    all_suggestions = tool.generate_purchase_suggestions(mock_combinations)
    print(f"\n🎯 All purchase suggestions: {len(all_suggestions)}")
    
    total_mismatches = 0
    for suggestion in all_suggestions:
        purchase_count = suggestion['total_cost'] // 100
        displayed_count = len(suggestion['combinations'])
        if purchase_count != displayed_count:
            print(f"   ❌ {suggestion['description']}: Expected {purchase_count}, got {displayed_count}")
            total_mismatches += 1
        else:
            print(f"   ✅ {suggestion['description']}: {purchase_count}組")
    
    if total_mismatches == 0:
        print(f"\n🎉 SUCCESS: All purchase patterns show correct combinations!")
    else:
        print(f"\n❌ FAILED: {total_mismatches} patterns have mismatched combinations")
    
    print(f"\n✅ Purchase patterns fix test completed")

if __name__ == "__main__":
    test_purchase_patterns_fix() 