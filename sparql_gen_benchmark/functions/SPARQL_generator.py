from .gpt_excute import excute_gpt
from .rdf_config_executer import create_strain_text, execute_rdf_config
from .text_extractor import extract_conditions_variables, extract_variable_names
import os
import re

def remove_specific_word_v2(query: str, word_to_remove: str) -> str:
    # SELECT と WHERE の間を正規表現で抽出
    pattern = re.compile(r"(SELECT\s+)(.*?)(\s+WHERE)", re.DOTALL)
    match = pattern.search(query)
    
    if match:
        select_part = match.group(1)
        middle_part = match.group(2)
        where_part = match.group(3)
        
        # 指定された単語を middle_part から削除
        cleaned_middle_part = middle_part.replace(word_to_remove, "").strip()
        
        # クエリを再構築（整形）
        cleaned_query = f"{query[:match.start(2)]}{cleaned_middle_part}{query[match.end(2):]}"
        return cleaned_query
    else:
        # マッチしない場合は元のクエリを返す
        return query
    

def sparql_gen(database: str, questions: list, verbose: bool = False):
    """
    Generate and execute SPARQL queries for a list of questions using GPT-4, and update each question with the results.
    """
    for question in questions:
        # Generate SPARQL queries using GPT-4 based on the filled prompt
        retry = 0
        max_retry = 3
        while retry < max_retry:
            try:
                llm_output = excute_gpt(question["prompt_filled"])

                # Extract variables and parameters from the GPT output
                variables = extract_variable_names(llm_output)
                if variables == []:
                    raise Exception("No variables found in the GPT output", variables)
                
                parameters = extract_conditions_variables(llm_output)
                if parameters == {}: 
                    raise Exception("No parameters found in the GPT output", parameters)

                if verbose:
                    print("###"*100)
                    print(f"llm_output: {llm_output}")
                    print("---"*10)
                    print(f"Variables: {variables}")
                    print("---"*10)
                    print(f"Parameters: {parameters}")

                # Create strain text and execute RDF configuration
                create_strain_text(database, question["id"], variables, parameters)
                rdf_result = execute_rdf_config(database, question["id"])

                for key in parameters.keys():
                    rdf_result = remove_specific_word_v2(rdf_result, "?"+key)
            
                # Update each question dictionary with the results
                question.update(
                    {
                        "llm_output": llm_output,
                        "llm_variable": variables,
                        "llm_parameter": parameters,
                        "llm_rdf_result": rdf_result,
                    }
                )

                break
            except Exception as e:
                print(f"Error: {e}")
                print(question["id"])

                # load os.environ["PATH_RDF_CONFIG"] + "config/" + database + "/sparql.yaml"
                path_config_sparql = os.environ["PATH_RDF_CONFIG"] + "config/" + database + "/sparql.yaml"
                with open(path_config_sparql, "r") as file:
                    config_sparql = file.read()
                
                print(f"Remove {question['id']} from {path_config_sparql}")
                if str(question["id"])+":" in config_sparql:
                    # remove after ID{question["id"]}
                    config_sparql = config_sparql.split(str(question["id"]))[0]
                    with open(path_config_sparql, "w") as file:
                        file.write(config_sparql)
                    print(f"{question['id']} removed from {path_config_sparql}")
                retry += 1


    # Since questions list is modified in place, return is not necessary unless needed for chaining or similar uses
    return questions


def generate_one_sparql(database: str, user_prompt: str, verbose: bool = False):
    """
    Generate and execute SPARQL queries for a list of questions using GPT-4, and update each question with the results.
    """
    # Generate SPARQL queries using GPT-4 based on the filled prompt
    retry = 0
    max_retry = 3
    rdf_result = None
    print(f"User's question: {user_prompt}")
    while retry < max_retry:
        try:
            llm_output = excute_gpt(user_prompt)

            # Extract variables and parameters from the GPT output
            variables = extract_variable_names(llm_output)
            print(f"Variables: {variables}")
            if variables == []:
                raise Exception("No variables found in the GPT output", variables)
            
            parameters = extract_conditions_variables(llm_output)
            print(f"Parameters: {parameters}")
            if parameters == {}: 
                raise Exception("No parameters found in the GPT output", parameters)

            if verbose:
                print("###"*100)
                print(f"llm_output: {llm_output}")
                print("---"*10)
                print(f"Variables: {variables}")
                print("---"*10)
                print(f"Parameters: {parameters}")

            # Create strain text and execute RDF configuration
            create_strain_text(database, "docker-test", variables, parameters)
            rdf_result = execute_rdf_config(database, "docker-test")

            for key in parameters.keys():
                rdf_result = remove_specific_word_v2(rdf_result, "?"+key)
            break
        except Exception as e:
            print(f"Error: {e}")
            retry += 1


    # Since questions list is modified in place, return is not necessary unless needed for chaining or similar uses
    return rdf_result
