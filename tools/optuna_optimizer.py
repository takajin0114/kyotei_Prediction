import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from kyotei_predictor.pipelines.kyotei_env import KyoteiEnvManager 