The following jupyter notebooks have a combination of different methods to test the models on different tasks:

Test_API_HF
This program tests the models using the InferenceAPI (requests) on the following tasks:
•	Summarization
•	Text Generation
•	QA with Context
•	QA for QA models
•	Zero shot classification

Test_LangChain
This program tests the models using the LangChain method on the following tasks:
•	Text Generation
•	Summarization
•	Question Answering
•	Quick Classification (With or No Label)  This method also saves the results "..\Test_Results\Test Results.xlsx" 

Test_Space
This program tests two spaces of language models hosted on HF: GPT Baker and RWKD, if the code is not working this might be due to an expired link of the space.
Tasks tested:
•	Text Generation
•	Summarization
•	Question Answering
•	Quick Classification (With Label)

Full_Test_Class_LLChain
The following program can be used to test a model on an individual task for Summarization, Text Generation and QA with context. It can also test a model on the 3 tasks and can do so for multiple models. If a full test is run, it will save the results on:
"..\Test_Results\Test Results.xlsx"

*Sample usages are included on the notebook.


Test_EX
This is an executable for testing using the Full_Test_Class_LLChain, is executed from the terminal with the program path and the file path
exmple:
PS C:\Folder> python PDF_Extract_EX.py "C:\Folder\Data"

It will test:
•	Text Generation
•	Summarization
•	Question Answering (Context)

The Sample data is a .csv format, with the first column as the input data (Model Name) and each row as a new sample, I have left 
"Test_Data" as a reference usage.

The test results will be save on "..\Test_Results\Test Results.xlsx" 


Test_Classification
Jupyter notebook used to create the test for classification questions with and without labels, this testing can be saved on the "..\Test_Results\Test Results.xlsx" 

Test_Classification_EX
Is the executalbe version of "Test_Classification", it saves and tests on each of the two classification tasks, executed as the example:
PS C:\Folder> python PDF_Extract_EX.py "C:\Folder\Data"

