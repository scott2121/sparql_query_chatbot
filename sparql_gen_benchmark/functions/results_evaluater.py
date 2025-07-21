from typing import Any, Dict, List, Tuple
import pandas as pd
from munkres import Munkres
import numpy as np
from scipy.optimize import linear_sum_assignment
from tqdm import tqdm
import hashlib


def dict_to_tuple(d):
    if isinstance(d, dict):
        return tuple(sorted((k, dict_to_tuple(v)) for k, v in d.items()))
    return d

def calculate_match_rate(pred: List[Any], act: List[Any]) -> float:
    total_elements = len(pred)
    matches = sum(1 for p, a in zip(pred, act) if p == a)
    return matches / total_elements if total_elements > 0 else 0

def column_similarity(col1: pd.Series, col2: pd.Series) -> float:
    set1 = set(dict_to_tuple(v) for v in col1)
    set2 = set(dict_to_tuple(v) for v in col2)
    intersection = len(set1 & set2)
    answer_size = len(set2)
    similarity = intersection / answer_size if answer_size > 0 else 0
    # print(f"Comparing columns:\n{col1.name} vs {col2.name}\nSimilarity: {similarity}")
    return similarity

def find_best_column_matches(df1: pd.DataFrame, df2: pd.DataFrame) -> List[tuple]:
    similarity_matrix = [
        [column_similarity(df1[col1], df2[col2]) for col2 in df2.columns]
        for col1 in df1.columns
    ]

    # print(f"Similarity Matrix:\n{similarity_matrix}")

    m = Munkres()
    indexes = m.compute([[1 - sim for sim in row] for row in similarity_matrix])
    matches = []
    used_columns = set()
    for row, column in indexes:
        if row < len(df1.columns) and column < len(df2.columns):
            matches.append(
                (df1.columns[row], df2.columns[column], similarity_matrix[row][column])
            )
            used_columns.add(column)
    for col1 in df1.columns:
        if not any(col1 == match[0] for match in matches):
            matches.append((col1, None, 0))
    for i, col2 in enumerate(df2.columns):
        if i not in used_columns:
            matches.append((None, col2, 0))
    # print(f"Best Column Matches:\n{matches}")
    return matches

def pad_rows(df1: pd.DataFrame, df2: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    max_len = max(len(df1), len(df2))
    df1_padded = df1.reindex(range(max_len)).fillna(value="missing")
    df2_padded = df2.reindex(range(max_len)).fillna(value="missing")
    # print(f"Padded DataFrames:\nDF1:\n{df1_padded}\n\nDF2:\n{df2_padded}")
    return df1_padded, df2_padded

def evaluate_nested_data(
    questions: List[Dict[str, Any]], answer: List[Dict[str, Any]]
) -> Dict[str, Any]:
    all_metrics = {}
    for q, a in zip(questions, answer):
        try:
            q_df = pd.DataFrame(q["results"]) if q["results"] else pd.DataFrame()
            q_df = q_df if q_df.empty else q_df.applymap(lambda x: x["value"])
            save_columns = [key for key in q["variables"] if key in q_df.columns]
            q_df = q_df[save_columns]

            a_df = pd.DataFrame(a["results"]) if a["results"] else pd.DataFrame()
            a_df = a_df if a_df.empty else a_df.applymap(lambda x: x["value"])
            save_columns = [key for key in q["variables"] if key in a_df.columns]
            a_df = a_df[save_columns]

            if not q_df.empty and not a_df.empty:
                q_df, a_df = pad_rows(q_df, a_df)
                column_matches = find_best_column_matches(q_df, a_df)
                row_match_rates = []
                for row_index in range(len(q_df)):
                    row_pred = q_df.iloc[row_index].tolist()
                    row_act = a_df.iloc[row_index].tolist()
                    row_match_rates.append(calculate_match_rate(row_pred, row_act))

                average_match_rate = sum(row_match_rates) / len(row_match_rates)
                all_metrics[q["id"]] = {
                    "average_match_rate": average_match_rate,
                    "column_matches": column_matches,
                }
            else:
                all_metrics[q["id"]] = {
                    "average_match_rate": 0,
                    "column_matches": {},
                }
        except Exception as e:
            print(f"Error processing ID {q['id']}: {e}")
            all_metrics[q["id"]] = {
                "average_match_rate": 0,
                "column_matches": {},
            }
    overall_average = {
        "overall_average_match_rate": sum(m["average_match_rate"] for m in all_metrics.values()) / len(all_metrics)
    }

    # 計算結果を見やすく表示
    # print(f"\nOverall Average Match Rate: {overall_average['overall_average_match_rate']}\n")
    # for q_id, metrics in all_metrics.items():
    #     print(f"ID: {q_id}")
    #     print(f"  Average Match Rate: {metrics['average_match_rate']}")
    #     print("  Column Matches:")
    #     for match in metrics["column_matches"]:
    #         print(f"    {match[0]} -> {match[1]}: {match[2]}")
    #     print("\n")

    return {"overall_average": overall_average, "id_metrics": all_metrics}


# Jaccard 係数をベクトル化して計算する関数
def jaccard_index_vectorized(df1: pd.DataFrame, df2: pd.DataFrame) -> np.ndarray:
    # print(df1.shape, df2.shape)
    # NaN を 0 に変換して計算

    df1_numeric = df1.fillna(np.inf).applymap(convert_to_numeric)
    df2_numeric = df2.fillna(np.inf).applymap(convert_to_numeric)

    df1_numeric = df1_numeric.astype(np.float64)
    df2_numeric = df2_numeric.astype(np.float64)

    # 列数を揃える（少ない方に np.inf を埋める）
    max_cols = max(df1_numeric.shape[1], df2_numeric.shape[1])

    # df1, df2 両方の列数を max_cols に揃える
    df1_aligned = np.pad(df1_numeric.values, ((0, 0), (0, max_cols - df1_numeric.shape[1])), constant_values=np.inf)
    df2_aligned = np.pad(df2_numeric.values, ((0, 0), (0, max_cols - df2_numeric.shape[1])), constant_values=np.inf)

    # 共通部分（交差）の計算、np.inf の場合は交差として数えない
    intersection = np.logical_and(
        np.equal(df1_aligned[:, np.newaxis, :], df2_aligned),
        (df1_aligned[:, np.newaxis, :] != np.inf) & (df2_aligned != np.inf)
    ).sum(axis=2)

    # 和集合の計算、np.inf は含めない
    union = (
        (df1_aligned[:, np.newaxis, :] != np.inf).sum(axis=2) +
        (df2_aligned != np.inf).sum(axis=1) -
        intersection
    )

    # Jaccard 係数を計算
    jaccard_matrix = intersection / union
    jaccard_matrix[union == 0] = 0  # ゼロ割りを避ける

    return jaccard_matrix

# 最大重みマッチングと平均スコアを計算する関数
def calculate_max_weight_matching(df1, df2):
    df1, df2 = pad_rows(df1, df2)
    # 類似度行列を計算
    similarity_matrix = jaccard_index_vectorized(df1, df2)

    row_sums = similarity_matrix.sum(axis=1)
    col_sums = similarity_matrix.sum(axis=0)

    # 全ての要素が0の行・列を除外するためのマスクを作成
    non_zero_row_mask = row_sums != 0
    non_zero_col_mask = col_sums != 0

    # 条件に基づき、ある座標が0以上で他は0の行・列を固定
    fixed_row_mask = (similarity_matrix > 0).sum(axis=1) == 1  # 1つの列だけが0以上
    fixed_col_mask = (similarity_matrix > 0).sum(axis=0) == 1  # 1つの行だけが0以上

    dynamic_row_mask = non_zero_row_mask & ~fixed_row_mask
    dynamic_col_mask = non_zero_col_mask & ~fixed_col_mask

    # 非ゼロかつ固定されていない部分をフィルタリング
    filtered_matrix = similarity_matrix[dynamic_row_mask][:, dynamic_col_mask]

    # `linear_sum_assignment` を最大化モードで実行
    row_ind, col_ind = linear_sum_assignment(filtered_matrix, maximize=True)

    # 元の行列に対応するインデックスに戻す
    original_row_ind = np.where(dynamic_row_mask)[0][row_ind]
    original_col_ind = np.where(dynamic_col_mask)[0][col_ind]

    # 固定された行・列のインデックスを取得
    fixed_row_ind = np.where(fixed_row_mask)[0]
    fixed_col_ind = np.where(fixed_col_mask)[0]

    # 対応するスコア（固定行・列のスコアも含む）
    matching_scores = similarity_matrix[original_row_ind, original_col_ind]
    if len(fixed_row_ind) > 0 and len(fixed_col_ind) > 0:
        # np.ix_ を使って行と列のペアを指定してスコアを取得
        fixed_scores = similarity_matrix[np.ix_(fixed_row_ind, fixed_col_ind)]
        matching_scores = np.concatenate((matching_scores, fixed_scores.ravel()))

    # 行数が異なる場合の補正 (ペアがないものは0)
    total_rows = max(len(df1), len(df2))
    avg_score = np.sum(matching_scores) / total_rows

    return matching_scores, avg_score

# DataFrameのハッシュを作成するための関数
def hash_dataframe(df: pd.DataFrame) -> str:
    df_str = df.to_string()
    return hashlib.md5(df_str.encode()).hexdigest()


# Fill missing values with np.inf and handle non-numeric data by hashing
def convert_to_numeric(value):
    # 数値型かどうかをチェックして、数値ならそのまま返し、文字列ならハッシュ化
    if pd.api.types.is_numeric_dtype(type(value)):
        return value  # 数値型はそのまま
    else:
        return hash(value) 

def evaluate_jaccard(
    questions: List[Dict[str, Any]], answers: List[Dict[str, Any]]
) -> Dict[str, Any]:
    all_metrics = {}
    cache = {}  # キャッシュを保存する辞書

    for q, a in tqdm(zip(questions, answers), total=len(questions), desc="Evaluating"):
        # if q.keys()に"results"がない場合スキップ
        if "results" not in q.keys():
            print(f"Skipping {q['id']} due to missing results.")
            all_metrics[q["id"]] = {"jaccard_score": 0}
            continue

        # 質問のDataFrame
        q_df = pd.DataFrame(q["results"]) if q["results"] else pd.DataFrame()
        q_df = q_df if q_df.empty else q_df.applymap(lambda x: x["value"] if isinstance(x, dict) and "value" in x else x)

        # 回答のDataFrame
        a_df = pd.DataFrame(a["results"]) if a["results"] else pd.DataFrame()
        a_df = a_df if a_df.empty else a_df.applymap(lambda x: x["value"] if isinstance(x, dict) and "value" in x else x)


        # print(q_df.shape, a_df.shape)

        # print(q_df)

        # print(a_df)
        # データフレームに列がない場合はスキップ
        if q_df.shape[0] == 0 or q_df.shape[1] == 0:
            print(f"Skipping {q['id']} due to empty columns.")
            all_metrics[q["id"]] = {"jaccard_score": 0}
            continue

        # DataFrameのハッシュを作成
        q_hash = hash_dataframe(q_df)
        a_hash = hash_dataframe(a_df)

        # ハッシュキーでキャッシュを確認
        cache_key = (q_hash, a_hash)
        if cache_key in cache:
            #print("Cache hit", q["id"])
            # キャッシュが存在する場合、キャッシュを使用
            jaccard_result = cache[cache_key]
        else:
            # 存在しない場合は計算し、キャッシュに保存
            #print("Cache miss", q["id"])
            jaccard_scores, avg_jaccard = calculate_max_weight_matching(q_df, a_df)
            jaccard_result = {"jaccard_score": avg_jaccard}
            cache[cache_key] = {"jaccard_score": avg_jaccard}

        all_metrics[q["id"]] = jaccard_result

    # print(len(all_metrics))
    # print(sum(m["jaccard_score"] for m in all_metrics.values()))
    # print(len( all_metrics.values()))
    overall_average = {
        "overall_average_jaccard_score": sum(m["jaccard_score"] for m in all_metrics.values()) / len(all_metrics),
    }

    return {**all_metrics, **overall_average}