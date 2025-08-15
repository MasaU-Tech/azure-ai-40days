from promptflow.core import tool

def _normalize(s: str) -> str:
    if s is None:
        return ""
    # 超簡易前処理：前後空白除去＋全角空白正規化＋改行/連続空白を1つに
    import re
    s = s.strip().replace("\u3000", " ")
    s = re.sub(r"\s+", " ", s)
    return s

@tool
def evaluate(answer: str, ground_truth: str) -> float:
    """
    極小コストのルールベース評価（0.0 or 1.0）
    - 完全一致（前処理後）が true → 1.0
    - それ以外は 0.0
    ※まずは配管確認用。後日、類似度などに差し替え可。
    """
    a = _normalize(answer)
    g = _normalize(ground_truth)
    return 1.0 if (a == g and g != "") else 0.0