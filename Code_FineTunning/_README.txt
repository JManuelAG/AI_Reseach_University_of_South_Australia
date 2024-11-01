This folder contains three different programs for the fine tunning of a model:

Create_DataSet
This program allows you to convert your .csv file in to a Data Set dictionary with Training, Testing, Validation sets to be push in to Hugging Face space. This is important as this is the format the fine tunning programs use.

Fine_Tunning_QLora_Classification
This program uses the QLora and PEFT methodology for fine tunning with the Transformers training library, this usage is particularly for classifications tasks. The training data needs to be change according to the task and the number of classes needs to be changed according to it.

Fine_Tunning_QLora_Classification
This program uses the QLora and PEFT methodology for fine tuning with the Transformers training library, this usage is particularly for summarisation tasks. 
