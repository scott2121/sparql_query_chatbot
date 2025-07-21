import json
import os


def make_prompt(
    database: str, prompt_id: int, prompt_variable_id: int, questions: list
):
    path_prompts = os.environ["PATH_DIR"] + os.environ["PATH_PROMPTS"]
    path_variables = os.environ["PATH_DIR"] + os.environ["PATH_VARIABLES"]

    # 指定されたファイルからJSONデータをロードします
    with open(path_prompts, "r") as f:
        prompts = json.load(f)
    with open(path_variables, "r") as f:
        variables = json.load(f)

    # JSONデータから特定のエントリを取得します
    prompts_database = [v for v in prompts if v["database"] == database]
    variable_database = [v for v in variables if v["database"] == database]

    if not prompts_database or not variable_database:
        raise ValueError(f"データベース {database} はJSONファイルに存在しません。")

    prompt = next((v for v in prompts_database if v["id"] == prompt_id), None)
    variable = next(
        (v for v in variable_database if v["id"] == prompt_variable_id), None
    )

    if not prompt or not variable:
        raise ValueError(
            f"ID {prompt_id} または {prompt_variable_id} のプロンプトまたは変数が見つかりません。"
        )

    # 質問ごとにプロンプトを生成
    results = []
    for question in questions:
        params = {**variable, **question}  # 変数と質問の辞書をマージします
        filled_prompt = fill_template_with_params(prompt, params)

        # 質問辞書に追加情報を追加します
        question["prompt_id"] = prompt_id
        question["prompt_variable_id"] = prompt_variable_id
        question["prompt_filled"] = filled_prompt
        results.append(question)

    return results


def fill_template_with_params(template, params):
    """
    テンプレートのプレースホルダーをユーザーから提供されたパラメータおよび変数で置き換えます。
    """
    text = template["prompt"]
    for input_field in template["variables"]:
        if input_field in params:
            text = text.replace(f"{{{input_field}}}", str(params[input_field]))
        else:
            raise ValueError(f"変数 {input_field} がパラメータに見つかりません。")

    # 埋められたプロンプトを評価します
    return text




def make_one_prompt(
    database: str, user_question: str
):
    path_prompts = os.environ["PATH_DIR"] + os.environ["PATH_PROMPTS"]
    path_variables = os.environ["PATH_DIR"] + os.environ["PATH_VARIABLES"]

    # 指定されたファイルからJSONデータをロードします
    with open(path_prompts, "r") as f:
        prompts = json.load(f)
    with open(path_variables, "r") as f:
        variables = json.load(f)

    # JSONデータから特定のエントリを取得します
    prompts_database = [v for v in prompts if v["database"] == database]
    variable_database = [v for v in variables if v["database"] == database]

    if database == 'uniprot':
        prompt_id = 2
        prompt_variable_id = 2
    elif database == 'rhea':
        prompt_id = 5
        prompt_variable_id = 4
    elif database == 'bgee':
        prompt_id = 6
        prompt_variable_id = 5

    prompt = next((v for v in prompts_database if v["id"] == prompt_id), None)
    variable = next(
        (v for v in variable_database if v["id"] == prompt_variable_id), None
    )

    variable["user_question"] = user_question

    final_prompt = prompt["prompt"]
    for _variable in prompt["variables"]:
        final_prompt = final_prompt.replace(f"{{{_variable}}}", variable[_variable])

    return final_prompt
