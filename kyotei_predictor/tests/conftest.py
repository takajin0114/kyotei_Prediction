# ルート tests 用 conftest
# Selenium 未導入時は web_display 系テストを収集しない（import エラーを防ぐ）
def pytest_ignore_collect(path, config):
    try:
        import selenium  # noqa: F401
        return False  # 収集する
    except ImportError:
        pass
    path_str = str(path)
    if "web_display" in path_str or "test_web_display" in path_str:
        return True  # 収集しない
    return False
