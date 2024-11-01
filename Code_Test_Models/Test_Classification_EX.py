from langchain import HuggingFaceHub, LLMChain
from langchain.prompts import PromptTemplate
import os
import json
os.environ["HUGGINGFACEHUB_API_TOKEN"] = "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"
import pandas as pd
import time 
import argparse

# *******************************************************************************************************************************************************************
# ************************ Building The Test ************************************************************************************************************************
#********************************************************************************************************************************************************************

# ************************************************************ SAVING DETAILS ***************************************************************************************
def save_test(answers, model, type_test):
    file_path = "../Test_Results/Test Results.xlsx"
    if type_test == 1:
        sheet_name = "class_lab"
    else:
        sheet_name = "class_no_lab"
    answers.insert(0, model)
    new_data = pd.DataFrame([answers])

    # Try to read the existing data
    try:
        existing_data = pd.read_excel(file_path, sheet_name=sheet_name)
    except FileNotFoundError:
        existing_data = pd.DataFrame()

    # Append new data
    updated_data = pd.concat([existing_data, new_data], ignore_index=True)
    updated_data = updated_data.drop_duplicates()

    # Write back to Excel
    with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        updated_data.to_excel(writer, sheet_name=sheet_name, index=False)

# ************************************************************ Building Promt *******************************************************************************************

template_no_label= """
From the follwoing text, can you classify the type of text to a relevant topic in Medicine.

Text: {question}

Answer:
"""

template_label= """
From the follwoing text, can you classify the type of text with one of the following labels:

Labels: : [ 'Digital Twin', 'Clinical Trail', 'Patient Study', 'AI in Health',   'Medical Recovery']

Text: {question}

Answer:
"""

templates = [template_no_label, template_label]

# ************************************************************ Run Model *******************************************************************************************
# Run the test on the model  
def run(model):
    hub_llm = HuggingFaceHub(repo_id=model, 
                            model_kwargs= {
                                "min_length": 5,
                                "max_length": 10,
                                "temperature": 1,
                                "top_p": 0.3,
                                "early_stopping": True,
                                "length_penalty": 1,
                                "num_beams": 5,
                                "no_repeat_ngram_size": 2,
                                "do_sample": True,  # False for summarisation
                                "repetition_penalty": 1.2,
                            },
                            huggingfacehub_api_token="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")
    type_test = 0
    for template in templates:
        prompt = PromptTemplate(
            input_variables=["question"],

            # ****** HERE IS WHERE PROMT NEEDS TO BE CHANGED FOR EACH TEST **********
            template= template
        )

        hub_chain = LLMChain(prompt=prompt, llm=hub_llm, verbose=True)

        # Testing
        answers = []
        attempts = 2
        for i in range(5):
            while attempts > 0:
                try:
                    question = data[i]['Abstract']
                    answer = hub_chain.run(question=question)
                    print("ANSWER:", answer)
                    answers.append(answer)
                    break
                except Exception as e:
                    attempts -= 1
                    if attempts == 0:
                        print("Model didn't work")
                    print(f"An error occurred: {e}. Retrying in 20 seconds...")
                    time.sleep(30)  # Wait for 30 seconds before retrying
            
        save_test(answers, model, type_test)
        type_test += 1

        # # Testing
        # answers = []
        # for i in range(5):
        #     question = data[i]['Abstract']
        #     answer = hub_chain.run(question = question)
        #     print(answer)
        #     answers.append("ANSWER:", answer)

        # save_test(answers, model, type_test)
        # type_test += 1

# *******************************************************************************************************************************************************************
# ************************ Input Implementaton with User ************************************************************************************************************
#********************************************************************************************************************************************************************
      
# ************************************************************ Reading Data *******************************************************************************************
# Get the directory of the current script
current_script_path = os.path.dirname(os.path.abspath(__file__))

# Change the current working directory to the script directory
os.chdir(current_script_path)
print(current_script_path)

# Replace 'your_file.json' with the path to your JSON file
file_path = '../Outputs/PDF_Articles/articles.json'

# Open the JSON file and load its contents
with open(file_path, 'r') as file:
    data = json.load(file)

# ************************************************************ Testing Models *******************************************************************************************
def main(file_path):
    # Read the .xlsx file
    df = pd.read_excel(file_path)

    # Only test models for text generation
    for model in df[~df.iloc[:,0].isna()].iloc[:,0]:
        try:
            print("\n\n------------------------------------- TESTING MODEL:", model)
            run(model)
        except:
            print(f"MODEL NOT WORKING: {model}")
            pass 


# ************************************************************ Run Program **********************************************************************************************
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run tests on models.")
    parser.add_argument('file_path', type=str, help="Path to the Excel file containing the models.")
    
    args = parser.parse_args()
    main(args.file_path)

