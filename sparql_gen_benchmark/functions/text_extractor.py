import re


def extract_variable_names(text):
    # Split the text into lines
    lines = text.split("\n")

    # Initialize a list to hold variable names
    variable_names = []

    # Flag to detect when to start collecting variable names
    collecting = False

    # Iterate through each line
    for line in lines:
        # Check if the line is the section we want to collect from
        if line.strip() == "variables to look for based on elements in [variables_info]:":
            collecting = True
            continue
        # Stop collecting when we reach the next section
        elif line.strip() == "2. Conditions":
            break

        # If collecting is True, collect the variable names
        if collecting:
            if line.strip().startswith("-"):
                # Extract the variable name, remove leading '-' and strip any surrounding whitespace
                variable_name = line.strip()[1:].strip()
                variable_names.append(variable_name)

    return variable_names


def extract_conditions_variables(text):
    # ネストされたカッコと単一のカッコ内の内容を抽出する正規表現
    pattern = r"\{+([^}]*)\}+"
    
    # カッコ内のテキストを抽出
    matches = re.findall(pattern, text)

    # 重複を排除するためにセットを使用
    unique_matches = set(matches)

    # 抽出した内容を辞書に変換
    result = {}
    for match in unique_matches:
        # カンマで分割してから、各要素をさらにコロンで分割
        entries = match.split(", ")
        for entry in entries:
            if ": " in entry:
                key, value = entry.split(": ")
                # 辞書に追加前に余計なダブルクォートを取り除く
                result[key.strip()] = value.strip().strip('"')
    return result