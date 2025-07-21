import os
import subprocess


# config/{database}/sparql.yamlに追記するテキストを生成
def create_strain_text(database, id, variables, parameters):
    path_config_sparql = (
        os.environ["PATH_RDF_CONFIG"] + "config/" + database + "/sparql.yaml"
    )
    # ヘッダー部分のテキスト生成
    header = f"\n{id}:\n  variables: ["
    header += ", ".join(variables)
    header += "]\n"
    
    if len(parameters) > 0:
        header += "  parameters:\n"
    # パラメータ部分のテキスト生成
    param_text = ""
    for key, value in parameters.items():
        if value.endswith("'") or ":" in value:
            param_text += f'    {key}: {value}\n'
        else:
            param_text += f'    {key}: "{value}"\n'

    param_text += "  options:\n    distinct: true\n\n"

    # save path_config_sparql to save_path
    with open(path_config_sparql, "a") as file:
        file.write(header + param_text)


# コマンドとそのパラメータをリストとして定義
def execute_rdf_config(database, id):
    command = f"bundle exec rdf-config --config config/{database} --sparql {id}"
    # 実行するディレクトリのパス
    directory_path = os.environ["PATH_RDF_CONFIG"]

    # subprocess.runを使用してコマンドを実行
    try:
        result = subprocess.run(
            command,
            check=True,
            text=True,
            capture_output=True,
            cwd=directory_path,
            shell=True,
        )
    except subprocess.CalledProcessError as e:
        print("エラーが発生しました:", e)  # エラー内容を表示

    return result.stdout
