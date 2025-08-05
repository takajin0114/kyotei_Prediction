# 3連単的中率向上のための実装方針

## 📋 目次
1. [現在の実装方針の評価](#現在の実装方針の評価)
2. [学習システムの更新方式](#学習システムの更新方式)
3. [推奨改善方針](#推奨改善方針)
4. [段階的改善計画](#段階的改善計画)
5. [期待される成果](#期待される成果)
6. [実装ガイド](#実装ガイド)

---

## 🎯 現在の実装方針の評価

### ✅ 良い点

#### **1. 段階的報酬設計の効果**
```python
# 現在の報酬設計
- 的中時: (払戻金-賭け金)×1.2
- 2着的中時: 0（損失なし）
- 1着的中時: -20（ペナルティ）
- 不的中時: -100（最大ペナルティ）
```

**成果**:
- **的中率**: 1.70%（理論値0.83%の約2倍）
- **学習効率**: 16.2倍
- **部分的中率**: 13.5%

#### **2. 統計的学習の活用**
```python
# 条件付き確率の学習
- 1着確率の学習
- 2着|1着の条件付き確率
- 3着|1着,2着の条件付き確率
- 艇間相関の学習
```

#### **3. 最適化システムの安定性**
- **Optuna**によるハイパーパラメータ最適化
- **継続的最適化**の実装
- **自動評価**システム

### ⚠️ 改善が必要な点

#### **1. 報酬安定性の課題**
```python
# 現在の問題
- 正の報酬率: 52.5%（目標70%以上）
- 極端な報酬値の頻度が高い
- 平均報酬: 4.83（目標20以上）
```

#### **2. 学習時間の制限**
```python
# 現在の設定
total_timesteps = 100000  # 10万ステップ
n_eval_episodes = 2000    # 評価エピソード
```

#### **3. モデル間の知識継承なし**
- 各試行は独立した学習
- 過去の学習結果を活用していない

---

## 🔄 学習システムの更新方式

### **強化学習（PPO）の更新方式**

**❌ 継続的更新ではなく、独立した試行**

```python
# 各試行は独立して学習
def objective(trial, data_dir, test_mode=False):
    # 毎回新しいモデルを作成
    model = PPO("MlpPolicy", train_env, **hyperparams)
    model.learn(total_timesteps=100000)  # ゼロから学習
```

**特徴**:
- **各試行は独立**: 毎回ゼロから学習開始
- **以前の学習結果を継承しない**: 新しいモデルインスタンス
- **Optunaによる最適化**: ハイパーパラメータの探索のみ

### **統計的学習（条件付き確率）の更新方式**

**✅ インクリメンタル更新対応**

```python
def learn_conditional_probabilities(self, existing_model_path=None):
    # 既存モデルファイルから統計値を復元
    if existing_model_path and os.path.isfile(existing_model_path):
        with open(existing_model_path, 'r', encoding='utf-8') as f:
            model_data = json.load(f)
        stats = model_data.get('stats', {})
        # 既存統計値を加算
        first_counts.update(stats.get('first_counts', {}))
        second_given_first.update(stats.get('second_given_first', {}))
        # ... 他の統計値も同様
```

**特徴**:
- **統計値の継承**: 既存の統計カウントを加算
- **インクリメンタル学習**: 新しいデータで統計値を更新
- **モデル保存・読み込み**: JSON形式で統計値を保存

### **Optunaスタディの継続性**

**✅ 既存スタディの継続対応**

```python
def optimize_graduated_reward(resume_existing=False):
    if resume_existing:
        # 既存スタディファイルを探す
        existing_studies = []
        for file in os.listdir("./optuna_studies"):
            if file.startswith(study_name) and file.endswith(".db"):
                existing_studies.append(file)
        
        if existing_studies:
            # 最新のスタディファイルを使用
            latest_study = sorted(existing_studies)[-1]
            storage_path = f"sqlite:///optuna_studies/{latest_study}"
    
    # スタディ作成（既存スタディの継続対応）
    study = optuna.create_study(
        direction="maximize",
        study_name=study_name,
        storage=storage_path,
        load_if_exists=True  # 既存スタディを読み込む
    )
```

**特徴**:
- **最適化履歴の継承**: 既存の試行結果を保持
- **ハイパーパラメータ履歴**: 過去の最適化結果を活用
- **継続的最適化**: 新しい試行を追加

---

## 🚀 推奨改善方針

### **Phase 1: 報酬設計の最適化（最優先）**

```python
# 改善された報酬設計
def calc_trifecta_reward_improved(action, arrival_tuple, odds_data, bet_amount=100):
    trifecta = action_to_trifecta(action)
    is_win = trifecta == arrival_tuple
    
    if is_win:
        # 的中報酬の強化
        odds_map = {tuple(o['betting_numbers']): o['ratio'] for o in odds_data}
        odds = odds_map.get(trifecta, 0)
        payout = odds * bet_amount
        reward = (payout - bet_amount) * 1.5  # 1.2 → 1.5
    else:
        # 部分的中の報酬化
        first_hit = trifecta[0] == arrival_tuple[0]
        second_hit = trifecta[1] == arrival_tuple[1]
        
        if first_hit and second_hit:
            reward = +10  # 0 → +10（報酬化）
        elif first_hit:
            reward = -10  # -20 → -10（ペナルティ緩和）
        else:
            reward = -80  # -100 → -80（ペナルティ緩和）
    
    return reward
```

**期待効果**:
- **的中報酬の強化**: 学習動機の向上
- **部分的中の報酬化**: 学習効率の改善
- **ペナルティの緩和**: 探索の促進

### **Phase 2: 学習時間の延長**

```python
# 改善された学習設定
def objective_improved(trial, data_dir, test_mode=False):
    # ハイパーパラメータ（現在と同じ）
    
    # 学習時間の延長
    if test_mode:
        total_timesteps = 20000   # テスト用
        n_eval_episodes = 200     # テスト用
    else:
        total_timesteps = 200000  # 10万 → 20万ステップ
        n_eval_episodes = 5000    # 2000 → 5000エピソード
    
    # より細かいハイパーパラメータ調整
    learning_rate = trial.suggest_float('learning_rate', 5e-6, 5e-3, log=True)
    batch_size = trial.suggest_categorical('batch_size', [64, 128, 256])  # 32を削除
    n_epochs = trial.suggest_int('n_epochs', 10, 25)  # 3-20 → 10-25
```

### **Phase 3: アンサンブル学習の導入**

```python
# アンサンブル学習の実装
class EnsembleTrifectaModel:
    def __init__(self):
        self.models = []
        self.weights = []
    
    def add_model(self, model, weight=1.0):
        self.models.append(model)
        self.weights.append(weight)
    
    def predict(self, state):
        predictions = []
        for model, weight in zip(self.models, self.weights):
            pred = model.predict(state)
            predictions.append((pred, weight))
        
        # 重み付き投票
        return self.weighted_voting(predictions)
    
    def weighted_voting(self, predictions):
        # 重み付き投票による統合予測
        pass
```

### **Phase 4: 継続的学習の実装**

```python
# 継続的学習の実装
def continue_learning_from_best(model_path, new_data, additional_steps=50000):
    # 最良モデルを読み込み
    best_model = PPO.load(model_path)
    
    # 新しいデータで継続学習
    best_model.learn(total_timesteps=additional_steps)
    
    # 更新されたモデルを保存
    updated_path = f"{model_path}_updated"
    best_model.save(updated_path)
    
    return updated_path
```

---

## 📈 段階的改善計画

### **Week 1: 報酬設計の最適化**

#### **Day 1-2: 新しい報酬設計の実装**
```python
# kyotei_predictor/pipelines/kyotei_env.py の修正
def calc_trifecta_reward_improved(action, arrival_tuple, odds_data, bet_amount=100):
    # 新しい報酬設計の実装
    pass
```

#### **Day 3-4: テスト実行・検証**
```bash
# テスト実行
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward \
  --test-mode \
  --data-dir kyotei_predictor/data/raw/2024-01
```

#### **Day 5-7: 効果測定**
- 報酬安定性の測定
- 的中率の変化確認
- 学習効率の評価

### **Week 2: 学習時間の延長**

#### **Day 1-3: 学習設定の調整**
```bash
# 20万ステップでの学習
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward \
  --total-timesteps 200000 \
  --data-dir kyotei_predictor/data/raw/2024-01
```

#### **Day 4-5: 評価エピソードの増加**
```bash
# 5000エピソードでの評価
python -m kyotei_predictor.tools.evaluation.evaluate_graduated_reward_model \
  --n-eval-episodes 5000
```

#### **Day 6-7: 性能向上の確認**
- 学習曲線の分析
- 収束性の評価
- 過学習の検証

### **Week 3: アンサンブル学習**

#### **Day 1-3: 複数モデルの学習**
```python
# アンサンブル学習の実装
ensemble_models = train_ensemble_models()
```

#### **Day 4-5: 統合予測システムの構築**
```python
# 予測統合システム
prediction_system = EnsemblePredictionSystem(ensemble_models)
```

#### **Day 6-7: 最終性能評価**
- アンサンブル効果の測定
- 予測精度の向上確認
- システム全体の評価

### **Week 4: 継続的学習**

#### **Day 1-3: 継続的学習の実装**
```python
# 継続的学習システムの構築
continuous_learning_system = ContinuousLearningSystem()
```

#### **Day 4-5: 自動更新システムの構築**
```python
# 自動更新システム
auto_update_system = AutoUpdateSystem()
```

#### **Day 6-7: システム統合・テスト**
- 全システムの統合
- 自動化テストの実行
- 性能監視システムの構築

---

## 🎯 期待される成果

### **段階的改善目標**

#### **Phase 1（報酬設計改善）**
- **的中率**: 1.70% → 2.5%
- **報酬安定性**: 52.5% → 70%
- **平均報酬**: 4.83 → 15

#### **Phase 2（学習時間延長）**
- **的中率**: 2.5% → 3.0%
- **学習効率**: 16.2倍 → 20倍
- **収束性**: 改善

#### **Phase 3（アンサンブル学習）**
- **的中率**: 3.0% → 3.5%
- **予測安定性**: 大幅向上
- **リスク分散**: 効果

#### **Phase 4（継続的学習）**
- **的中率**: 3.5% → 4.0%
- **学習効率**: 継続的改善
- **適応性**: 向上

### **最終目標**
- **的中率**: 4.0%以上
- **報酬安定性**: 80%以上
- **平均報酬**: 30以上
- **学習効率**: 25倍以上

---

## 🔧 実装ガイド

### **1. 報酬設計の改善実装**

```python
# kyotei_predictor/pipelines/kyotei_env.py
def calc_trifecta_reward_improved(action, arrival_tuple, odds_data, bet_amount=100):
    """
    改善された段階的報酬設計
    """
    trifecta = action_to_trifecta(action)
    is_win = trifecta == arrival_tuple
    
    if is_win:
        # 的中報酬の強化
        odds_map = {tuple(o['betting_numbers']): o['ratio'] for o in odds_data}
        odds = odds_map.get(trifecta, 0)
        payout = odds * bet_amount
        reward = (payout - bet_amount) * 1.5
    else:
        # 部分的中の報酬化
        first_hit = trifecta[0] == arrival_tuple[0]
        second_hit = trifecta[1] == arrival_tuple[1]
        
        if first_hit and second_hit:
            reward = +10  # 2着的中の報酬化
        elif first_hit:
            reward = -10  # 1着的中のペナルティ緩和
        else:
            reward = -80  # 不的中のペナルティ緩和
    
    return reward
```

### **2. 学習時間延長の実装**

```python
# kyotei_predictor/tools/optimization/optimize_graduated_reward.py
def objective_improved(trial, data_dir, test_mode=False):
    # ハイパーパラメータの提案（改善版）
    learning_rate = trial.suggest_float('learning_rate', 5e-6, 5e-3, log=True)
    batch_size = trial.suggest_categorical('batch_size', [64, 128, 256])
    n_steps = trial.suggest_categorical('n_steps', [2048, 4096, 8192])
    gamma = trial.suggest_float('gamma', 0.95, 0.999)
    gae_lambda = trial.suggest_float('gae_lambda', 0.9, 0.99)
    n_epochs = trial.suggest_int('n_epochs', 10, 25)
    clip_range = trial.suggest_float('clip_range', 0.1, 0.3)
    ent_coef = trial.suggest_float('ent_coef', 0.0, 0.05)
    vf_coef = trial.suggest_float('vf_coef', 0.5, 1.0)
    max_grad_norm = trial.suggest_float('max_grad_norm', 0.3, 0.8)
    
    # 学習時間の延長
    if test_mode:
        total_timesteps = 20000
        n_eval_episodes = 200
    else:
        total_timesteps = 200000  # 延長
        n_eval_episodes = 5000    # 延長
    
    # モデル学習と評価
    model = PPO("MlpPolicy", train_env, **hyperparams)
    model.learn(total_timesteps=total_timesteps)
    eval_results = evaluate_model(model, eval_env, n_eval_episodes=n_eval_episodes)
    
    return eval_results['hit_rate'] * 100 + eval_results['mean_reward'] / 1000
```

### **3. アンサンブル学習の実装**

```python
# kyotei_predictor/tools/ensemble/ensemble_model.py
class EnsembleTrifectaModel:
    def __init__(self):
        self.models = []
        self.weights = []
    
    def add_model(self, model, weight=1.0):
        self.models.append(model)
        self.weights.append(weight)
    
    def predict(self, state):
        predictions = []
        for model, weight in zip(self.models, self.weights):
            pred = model.predict(state)
            predictions.append((pred, weight))
        
        return self.weighted_voting(predictions)
    
    def weighted_voting(self, predictions):
        # 重み付き投票による統合予測
        weighted_sum = 0
        total_weight = 0
        
        for pred, weight in predictions:
            weighted_sum += pred * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0
    
    def train_ensemble(self, data_dir, n_models=3):
        """複数モデルの学習"""
        for i in range(n_models):
            model = self.train_single_model(data_dir, model_id=i)
            self.add_model(model, weight=1.0)
```

### **4. 継続的学習の実装**

```python
# kyotei_predictor/tools/continuous/continuous_learning.py
class ContinuousLearningSystem:
    def __init__(self, base_model_path):
        self.base_model_path = base_model_path
        self.current_model = None
        self.learning_history = []
    
    def load_best_model(self):
        """最良モデルを読み込み"""
        self.current_model = PPO.load(self.base_model_path)
        return self.current_model
    
    def continue_learning(self, new_data, additional_steps=50000):
        """継続学習の実行"""
        if self.current_model is None:
            self.load_best_model()
        
        # 新しいデータで継続学習
        self.current_model.learn(total_timesteps=additional_steps)
        
        # 学習履歴を記録
        self.learning_history.append({
            'timestamp': datetime.now().isoformat(),
            'additional_steps': additional_steps,
            'data_size': len(new_data)
        })
        
        return self.current_model
    
    def save_updated_model(self, output_path=None):
        """更新されたモデルを保存"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"{self.base_model_path}_updated_{timestamp}"
        
        self.current_model.save(output_path)
        return output_path
```

---

## 📊 監視・評価指標

### **主要評価指標**

1. **的中率** (Hit Rate)
   - 目標: 4.0%以上
   - 現在: 1.70%

2. **報酬安定性** (Reward Stability)
   - 目標: 80%以上
   - 現在: 52.5%

3. **平均報酬** (Mean Reward)
   - 目標: 30以上
   - 現在: 4.83

4. **学習効率** (Learning Efficiency)
   - 目標: 25倍以上
   - 現在: 16.2倍

### **監視システム**

```python
# kyotei_predictor/tools/monitoring/performance_monitor.py
class PerformanceMonitor:
    def __init__(self):
        self.metrics = {}
    
    def track_metrics(self, model_path, eval_results):
        """性能指標の追跡"""
        self.metrics[model_path] = {
            'timestamp': datetime.now().isoformat(),
            'hit_rate': eval_results['hit_rate'],
            'mean_reward': eval_results['mean_reward'],
            'reward_stability': eval_results['positive_reward_rate'],
            'learning_efficiency': eval_results['learning_efficiency']
        }
    
    def generate_report(self):
        """性能レポートの生成"""
        # レポート生成ロジック
        pass
```

---

## 🎯 結論

**現在の実装方針は基本的に良い**ですが、以下の改善が必要です：

### **✅ 継続すべき方針**
1. **段階的報酬設計**（効果あり）
2. **統計的学習**（有効）
3. **Optuna最適化**（安定）

### **🚀 優先的に改善すべき方針**
1. **報酬設計の最適化**（最優先）
2. **学習時間の延長**（高効果）
3. **アンサンブル学習**（安定性向上）
4. **継続的学習**（長期的改善）

**現在の実装方針をベースに、段階的な改善を進めることで、3連単的中率を4%以上まで向上させることが可能**と判断します。

---

**作成日**: 2025-08-05  
**バージョン**: 1.0  
**作成者**: AI Assistant  
**更新履歴**: 初版作成 