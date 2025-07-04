from kyotei_predictor.pipelines.db_integration import KyoteiDB
from collections import defaultdict
import matplotlib.pyplot as plt

def calc_course_win_rate(db: KyoteiDB) -> dict:
    """コース別1着回数・勝率を集計"""
    total = defaultdict(int)
    wins = defaultdict(int)
    for race in db.fetch_all_races():
        results = db.fetch_results_by_race(race['race_id'])
        for r in results:
            total[r['pit_number']] += 1
            if r['arrival'] == 1:
                wins[r['pit_number']] += 1
    return {pit: wins[pit] / total[pit] if total[pit] else 0 for pit in range(1, 7)}

def calc_course_avg_time(db: KyoteiDB) -> dict:
    """コース別平均タイムを集計（欠損値除外）"""
    total_time = defaultdict(float)
    count = defaultdict(int)
    for race in db.fetch_all_races():
        results = db.fetch_results_by_race(race['race_id'])
        for r in results:
            if r['total_time'] is not None:
                total_time[r['pit_number']] += r['total_time']
                count[r['pit_number']] += 1
    return {pit: total_time[pit] / count[pit] if count[pit] else 0 for pit in range(1, 7)}

def plot_course_stats(db: KyoteiDB):
    win_rate = calc_course_win_rate(db)
    avg_time = calc_course_avg_time(db)
    courses = list(range(1, 7))
    win_rates = [win_rate[pit] for pit in courses]
    avg_times = [avg_time[pit] for pit in courses]

    fig, ax1 = plt.subplots()
    color = 'tab:blue'
    ax1.set_xlabel('コース番号')
    ax1.set_ylabel('1着率', color=color)
    ax1.bar(courses, win_rates, color=color, alpha=0.6, label='1着率')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.set_xticks(courses)

    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('平均タイム', color=color)
    ax2.plot(courses, avg_times, color=color, marker='o', label='平均タイム')
    ax2.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()
    plt.title('コース別1着率・平均タイム')
    plt.show()

# --- 利用例 ---
# db = KyoteiDB()
# print('コース別勝率:', calc_course_win_rate(db))
# print('コース別平均タイム:', calc_course_avg_time(db))
# plot_course_stats(db)
# db.close() 