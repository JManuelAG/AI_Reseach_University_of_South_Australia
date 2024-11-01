from langchain import HuggingFaceHub, LLMChain
from langchain.prompts import PromptTemplate
import os
import warnings
import time
import pandas as pd
from openpyxl import load_workbook
import argparse

# *******************************************************************************************************************************************************************
# ************************ Class Testing the Models *****************************************************************************************************************
#********************************************************************************************************************************************************************

class LLMTemplateTester:
    def __init__(self, repo_id):
        os.environ["HUGGINGFACEHUB_API_TOKEN"] = "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"
        # Ignore specific FutureWarnings
        warnings.filterwarnings("ignore", category=FutureWarning, module="huggingface_hub.utils._deprecation")
        self.repo_id = repo_id
        self._model_kwargs = {
            "min_length": 10,
            "max_length": 60,
            "temperature": 1,
            "top_p": 0.3,
            "early_stopping": True,
            "length_penalty": 1,
            "num_beams": 5,
            "no_repeat_ngram_size": 2,
            "do_sample": True,  # False for summarisation
            "repetition_penalty": 1.2,
            }
        
        self._tests = ["question", "summarize", "qa"]
        self.current_state = "question"

        # Read data 
        with open('../Datasets/Medical_Documents/test.dat', 'r') as file:
            self.lines = file.readlines()

    @property
    def model_kwargs(self):
        return self._model_kwargs

    @model_kwargs.setter
    def model_kwargs(self, new_kwargs):
        for key, value in new_kwargs.items():
            self._model_kwargs[key] = value
        self._setup_hub()

    # Function that changes the state based on the type of test is doing
    def set_current_state(self, test):
        self.current_state = test
        self.set_template()
        self.set_questions()
        self.set_contexts()

    # Chose the prompt template that will be used
    def set_template(self):
        templates = {
            "question": "Answer the question: {question}",
            "summarize": "Summarize the text: {question}",
            "qa": "From the following context text answer the question. If you don't know answer I don't know.\nContext: {context}\nQuestion: {question}"
            }
        self.template = templates[self.current_state]

    # Chose the question from the templates 
    def set_questions(self):
        test_questions = {
            "qa": [
                "What's my name?",
                "How many patient files?",
                "Give me the insights?",
                "What is the problem?"
                ],
            "summarize": [
                self.lines[5099],  
                self.lines[2197],  
                self.lines[0]      
                ],
            "question": [
                "What are ICD-10 codes used for?",
                "Who is Elton John?",
                "What’s clinical NLP?",
                "What are the Symptoms of Malaria?",
                "What is the ICD10 code of Malaria?"
                ]
            }
        self.questions = test_questions[self.current_state]

    # Set the context for the type of text, some context are empty 
    def set_contexts(self):
        test_context = {
            "qa": [
                "My name is Clara and I live in Berkeley.",
                self.lines[0], self.lines[0], self.lines[0]],
            "summarize": ["", "", ""],
            "question": ["", "", "", "", ""]
        }
        self.contexts = test_context[self.current_state]
    
    def _setup_hub(self):
        self.hub_llm = HuggingFaceHub(repo_id=self.repo_id, 
                                      model_kwargs=self._model_kwargs)
    
    def set_prompt(self):
        # Set up promp template base on the type of test  [question, summarize, qa]                 
        self.prompt = PromptTemplate(
            input_variables=["question", "context"],
            template= self.template # template will vary base on the test [question, summarize, qa]
            )
        self.set_chain()
    
    def set_chain(self):
        verbose = False
        # Verbose changes for summarization 
        if self.current_state == "summarize":
            verbouse = True
        # Set up chain
        self.hub_chain = LLMChain(prompt=self.prompt, 
                                  llm=self.hub_llm, 
                                  verbose=verbose # True for summarization
                                  )
    
    # Start running the test based on the type of task or all of them
    def run_test(self, test="all"):
        # All tests
        if test == "all":
            for test in self._tests:
                self.run_test2(test)

        # Test on a specific area 
        else:
            self.run_test2(test)
    
    # Run the chain and save the answers
    def run_test2(self, test):
        if test == "summarize":
            self.model_kwargs = {"do_sample": True}
        else:
            self.model_kwargs = {"do_sample": False}
        
        self.set_current_state(test)
        self.set_prompt()

        print(f"\n******* TEST FOR {self.current_state} **********")
        answers = []
        for context, question in zip(self.contexts, self.questions):
            answer = self.run_chain(context=context, question=question)
            if test != "summarize":
                print("\nQustion: ", question)
            print("Answer:", answer)
            answers.append(answer)
        self.save_test(answers)
    
    # User interaction with the model for a one use only 
    def pipeline(self, test = "question", question = " ", context = " "):
        if test == "summarize":
            self.model_kwargs = {"do_sample": True}
        else:
            self.model_kwargs = {"do_sample": False}
        self.set_current_state(test)
        self.set_prompt()
        answer = self.run_chain(context=context, question=question)
        if test != "summarize":
                print("\nQustion: ", question)
        print("Answer:", answer)

    # Runs the chain and gives 2 different attemps waiting for the model to start up
    def run_chain(self, context, question):
        attempts = 2
        while attempts > 0:
            try:
                answer = self.hub_chain.run(context=context, question=question)
                return answer
            except Exception as e:
                attempts -= 1
                if attempts == 0:
                    print("Model didn't work")
                    return  "Model didn't work"
                print(f"An error occurred: {e}. Retrying in 20 seconds...")
                time.sleep(20)  # Wait for 20 seconds before retrying
    
    # Save the test on the result file
    def save_test(self, answers):
        file_path = "../Test_Results/Test Results.xlsx"
        sheet_name = self.current_state
        answers.insert(0, self.repo_id)
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

# *******************************************************************************************************************************************************************
# ************************ Input Implementaton with User ************************************************************************************************************
#********************************************************************************************************************************************************************
            
# Get the directory of the current script
current_script_path = os.path.dirname(os.path.abspath(__file__))

# Change the current working directory to the script directory
os.chdir(current_script_path)
print(current_script_path)


def main(file_path):
    # Read the .xlsx file
    df = pd.read_excel(file_path)

    # Only test models for text generation
    for model in df[~df.iloc[:,0].isna()].iloc[:,0]:
        try:
            print("\n\n------------------------------------- TESTING MODEL:", model)
            test = LLMTemplateTester(repo_id=model)
            test.run_test()
        except:
            print(f"MODEL NOT WORKING: {model}")
            pass 


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run tests on models.")
    parser.add_argument('file_path', type=str, help="Path to the Excel file containing the models.")
    
    args = parser.parse_args()
    main(args.file_path)


        