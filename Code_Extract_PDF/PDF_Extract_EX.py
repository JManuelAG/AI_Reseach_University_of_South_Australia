import requests
import xml.etree.ElementTree as ET
import re
import json

import nltk
from nltk.corpus import words
nltk.download('words')

import subprocess
import os 
import shutil
import argparse

# *******************************************************************************************************************************************************************
# ************************ PROCESS FILES ON CERMINE AND MOVE TO OUTPUT FOLDER ***************************************************************************************
#********************************************************************************************************************************************************************

# Set up argparse to accept a folder path as a command-line argument
parser = argparse.ArgumentParser(description="Process a folder path.")
parser.add_argument('folder_path', type=str, help="Path to the folder")

args = parser.parse_args()

# The folder location chosen by the user
src = args.folder_path

# Get the directory of the current script
current_script_path = os.path.dirname(os.path.abspath(__file__))

# Change the current working directory to the script directory
os.chdir(current_script_path)
print(current_script_path)

# Paths should be raw strings to handle backslashes correctly
jar = "./Cermine_Java/cermine-impl-1.13-jar-with-dependencies.jar"

# Construct the command
command = ['java', '-cp', jar, 'pl.edu.icm.cermine.ContentExtractor', '-path', src, '-outputs', 'jats,text']

# Run the command
subprocess.run(command)

target_dir_xml = "./Outputs/Xml"
target_dir_txt = "./Outputs/Txt"

# Function to clear the contents of a directory
def clear_directory(directory):
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')

# Clear directories
clear_directory(target_dir_txt)
clear_directory(target_dir_xml)

# Create target directories if they don't exist (in case they were removed)
os.makedirs(target_dir_txt, exist_ok=True)
os.makedirs(target_dir_xml, exist_ok=True)

# Move files
for filename in os.listdir(src):
    file_path = os.path.join(src, filename)
    
    # Check and move .cermtxt files
    if filename.endswith('.cermtxt'):
        shutil.move(file_path, os.path.join(target_dir_txt, filename))
    
    # Check and move .cermxml files
    elif filename.endswith('.cermxml'):
        shutil.move(file_path, os.path.join(target_dir_xml, filename))


# *******************************************************************************************************************************************************************
# ************************ EXTRACTION DESIGN ON TEXT AND XML *********************************************************************************************************
#********************************************************************************************************************************************************************

def get_root(file):
    tree = ET.parse(file)
    root = tree.getroot()
    return root


# ****************************************** TEXT FORMATING AND CLEANING *********************************************************************************************
      
def remove_duplicate_lines(file_path):
    seen_lines = set()
    unique_lines = []

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            clean_line = line.strip()
            if clean_line not in seen_lines:
                seen_lines.add(clean_line)
                unique_lines.append(line.strip())  # Keep the original line, including whitespace

    return unique_lines

def clean_sentence(sentence):
    # Remove numbers
    sentence = re.sub(r'\d+', ' ', sentence)

    # Remove special characters (excluding basic punctuation)
    sentence = re.sub(r'[^a-zA-Z\s,.?!()]', '', sentence)

    return sentence

def is_mostly_english(text, english_words, threshold=0.6):
    """
    Checks if most of the words in the text are English.
    
    :param text: The text to be checked.
    :param threshold: The fraction of words that need to be English.
    :return: True if the condition is met, False otherwise.
    """
    english_words = set(words.words())
    long_words = 0

    try:
        words_in_text = text.split()
        english_count = sum(1 for word in words_in_text if word.lower() in english_words)
    except:
        return text

    try:
        words_in_text = text.split()

        # Check for words that are longer of 20 characters 
        for word in words_in_text:
            if len(word) > 20:
                long_words += 1
    except:
        return text

    # Thresholds for english content and long words
    if not (english_count / len(words_in_text) >= threshold) or (long_words > 2):
        return "none"
    else:
        return text 
    
def remove_noise(text):
    """
    The following function removes any noise present in the abstract from the first look of the abstract in the elememnt "Abstract" of the Xml
    """
    # Define regex patterns for email and website URL
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    website_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'

    # Split the text into words
    words = text.split()

    # FIRST PART REMOVE SINGLE ITEMS
    i = 0

    for i in range(0, len(words//4)):
        if len(words[i]) < 2 and len(words[i+1]) < 2:
            pass
        else:
            break

    words = words[i:]

    # Check if any of the first 10 words is an email or website
    for i, word in enumerate(words[:10]):
        if re.fullmatch(email_pattern, word) or re.search(website_pattern, word):
            # Return the text from the email or website onwards
            return ' '.join(words[i+1:])

    # If no email or website is found in the first 10 words, return the original text
    return " ".join(words)

def format_paragraph(paragraph):
    # Remove existing line breaks
    paragraph = paragraph.replace('\n', ' ')

    # Add a line break after each period that ends a sentence
    paragraph = re.sub(r'(\.\s)(?=[A-Za-z])', r'.\n', paragraph)

    return paragraph

# ********************************************** ABSTRACT EXTRACTION FUNCTIONS *****************************************************************************************

def get_abstract_element(root):
    """
    Initial look of the abstract by the element "abstract"
    """
    # This will try to find abstract as a found element on the XML
    try:
        if type(root.find('.//abstract/p').text) != None and len(root.find('.//abstract/p').text) > 30:
            text = root.find('.//abstract/p').text
            abstract = text
            abstract = remove_noise(abstract)
            return abstract
    except:
        return 'none' 
    

def get_abstract(root):
    """
    Second look of the abstract by looking for word abstract on the different sections of the Xml
    """
    abstract = "none"
    abs_state = 0
    abs_sec = 0

    # This will look for the abstract on the XML sections (outside of the metadata)
    if abs_state == 0:
        for sec in root.findall('.//sec'):
            sec_id = sec.get('id')  # Get the 'id' attribute of the <sec> element
            
            for itr in sec:
                
                # Test look at iterations
                #print(itr.tag)
                
                # When to stop recording
                if (abs_state == 1) and (

                    # Word starts with keyword, something different
                    (itr.text.strip().startswith(("ARTICLE HISTORY", "Keywords:", "KEYWORDS"))) or 
                    
                    # Changes of section
                    (abs_sec != sec_id) or 
                    
                    # It becomes a tittle
                    (itr.tag == 'title')
                ):
                    break
                    
                # Continue recording (Extra if conditions just in case)
                elif abs_sec == sec_id and abs_state == 1 and itr.tag == 'p':
                    abstract += '\n' + itr.text

                # First condition to find word abstract and change state to start recording
                if itr.text.strip().startswith(("Abstract", "ABSTRACT", "TECHNICAL ABSTRACT", "A B S T R A C T", "Executive Summary", 'a b s t r a c t')) and abs_state == 0:
                    abstract = itr.text
                    abs_state = 1
                    abs_sec = sec_id


            #article['Abstract'] = abstract
            if abs_state == 1:
                break

    return abstract


def get_abstract_text(file):
    """
    Third option at looking for abstract in the text file
    """
    try:
        text = remove_duplicate_lines(file)
    except:
        return "Did not read"

    abstract = "none"
    abs_state = 0
    num_paragraphs = 0

    # Regex pattern to match initials (like "S. " or "L. A. ")
    initials_pattern = re.compile(r'\b[A-Z]\. ?[A-Z]?\.?')

    for sentence in text:
      

        # sentence = clean_sentence(sentence) 
        stop_characters = ["©", "*"]

        # Stopping conditions for Introduction
        if sentence.strip().startswith(("Introduction", "1 Introduction", "1. Introduction", ' 1 1.1 INTRODUCTION',  'I N T R O D U C T I O N')) and abs_state == 1:
            abs_state = 0

        # Stop keyword found after 5 paragraphs
        elif sentence.strip().startswith(("ARTICLE HISTORY", "Keywords:", "KEYWORDS", "Key", 'K E Y W O R D S', 'KXeywords')) and num_paragraphs > 5:
            abs_state = 0

        # Stops if © found on sentence after 5 sentences
        elif "©"  in sentence and num_paragraphs > 5:
            abs_state = 0

        # Stops if © found on sentence after 5 sentences
        elif "*"  in sentence and num_paragraphs > 5:
            abs_state = 0

        # Stops if found a figure, means I went on the text     
        elif "Fig." in sentence and abs_state == 1:
            print("You went on the text!!!!!!!")
            abs_state = 0

        # Max Len of Paragraphs    
        elif num_paragraphs > 30:
            abs_state = 0
        
        # More than 2 words all capital letters
        elif re.match(r'^([A-Z]{2,}\s+){1,}[A-Z]{2,}', sentence.strip()) and num_paragraphs > 5:
            abs_state = 0

        
        exclude_chars = ["@", "#"]
        
        # Starting conditions 
        if abs_state == 1 and not any(
            
            # Ecluding @ from sentence
            char in sentence for char in exclude_chars) and (

                # Excluding sentence with more than 7 numbers
                len(re.findall(r'\d', sentence)) <= 4) and not (
                    
                    # Excluding Names from sentence L. follow by something
                    initials_pattern.search(sentence)) and not (
                        
                        # More than 2 numbers starting 
                        re.match(r'^\d{2,}', sentence.strip())):
            
            # Add a paragraph
            num_paragraphs += 1
            abstract += '\n' + sentence

        if sentence.strip().startswith(("Abstract", "ABSTRACT", "TECHNICAL ABSTRACT", "A B S T R A C T", "Executive Summary", 'a b s t r a c t')) and abs_state == 0:
            abs_state = 1
            abstract = sentence

        


    return abstract

def get_abstract_last(root, english_words):
        """
        Last option when Abstract is not found or present, It will look for Introduction or the first paragraph
        """

        abstract = ""
        num_paragraphs = 0
        exclude_chars = ["@", "#", "©", "*"]
        # Regex pattern to match initials (like "S. " or "L. A. ")
        initials_pattern = re.compile(r'\b[A-Z]\. ?[A-Z]?\.?')

        for sections in root.findall(".//sec"):
                for sec in sections:
                        for sentence in sec.text.split("\n"):
                                        if num_paragraphs < 40 and not any(
                                                
                                                # Ecluding @ from sentence
                                                char in sentence for char in exclude_chars) and (
                                                        
                                                        # Excluding sentence with more than 7 numbers
                                                        len(re.findall(r'\d', sentence)) <= 4) and not (
                                                        
                                                        # Excluding Names from sentence L. follow by something
                                                        initials_pattern.search(sentence)) and not (
                                                                
                                                                # More than 2 numbers starting 
                                                                re.match(r'^\d{2,}', sentence.strip())) and not (

                                                                        # Exclude website links
                                                                        re.compile(r'https?://\S+|www\.\S+|\S+\.com').search(sentence)) and not (
                                                                        
                                                                        # Eclude tems and condition
                                                                        "Terms & Conditions" in sentence):
                                                
                                                # Add a paragraph
                                                num_paragraphs += 1
                                                abstract += '\n' + sentence

                
                # Test if the paragraphs collected are good 
                try:
                        abstract = is_mostly_english(abstract, english_words)
                        if len(abstract.split()) > 25:
                                break
                                
                        else:
                                abstract = ""
                except:
                        abstract = ""
                
                        
                
        return abstract

# ******************************************************** ALL ELEMENTS EXTRACTION AND ADDING TO A DICTIONARY *******************************************************
def add_author(article, name, email=None, affiliation=None):
    """
    Adds an author and detials to the dictionary of the research
    """
    new_author = {
        "Name": name,
        "Email": email if email else "none",
        "Affiliation": affiliation if affiliation else []
    }
    article['Author'].append(new_author)

# Extract all deatils to a new dictionary
def get_details(root, file, english_words):
    # Template structure
    article = {
        "Tittle" : "none",
        "Year": "none",
        "ID": "none",
        "Author": [],
        "Affiliations": {},
        "Abstract": ""
    }

    # State variables
    affilitations = {}
    aff_stat = 0
    abstract = ''
    
    # Extract article title
    try:
        article_title = root.find('.//article-title').text
        article['Tittle'] = article_title
        #article['Tittle'] = clean_sentece(article_title)
    except:
        pass

    # Extract Year
    try:
        year = root.find('.//pub-date/year').text
        article['Year'] = year
    except:
        pass

    # Extract DOI
    try:
        art_id = root.find('.//article-id').text
        article['ID'] = art_id
    except:
        pass

    # Find all Affilitaions
    try:
        for affiliation in root.findall('.//aff'):
            aff_stat = 1
            id = affiliation.get('id')
            institution = affiliation.find('institution').text
            affilitations[id] = institution

        article["Affiliations"] = affilitations
    except:
        pass

    # Find Name, Email, add Affiliations
    for author in root.findall('.//contrib[@contrib-type="author"]'):
        name = ""
        email = ""
        affiliation = []
        try:
            name = author.find('string-name').text
        except:
            pass

        try:
            email = author.find('email').text
        except:
            pass
        try:        
            if aff_stat == 1:
                for aff in author.findall('.//xref'):
                    id = aff.get('rid')
                    affiliation.append(affilitations[id])
        except:
            pass
    
        add_author(article, name, email, affiliation)
    
    # ABSTRACT EXTRACTIONS  
    # ALL EXTRACTIONS FOLLOW AN EGLISH READABILITY TEST AND A MINIMUM 50 WORDS LENGTH
    # Method 1 get_abstract
    abstract = get_abstract(root)

    abstract = is_mostly_english(abstract, english_words)

    # Method 2 get_abstract_element
    try:
        if len(abstract.split()) < 50 or abstract == 'none':
            abstract = get_abstract_element(root)
    except:
        abstract = get_abstract_element(root)
    
    abstract = is_mostly_english(abstract, english_words)

    # Method 3 get_abstract_text
    try:
        if len(abstract.split()) < 50 or abstract == 'none':
            abstract = get_abstract_text(file)
    except:
        abstract = get_abstract_text(file)
    
    abstract = is_mostly_english(abstract, english_words)

    # Method 4 get_abstract_last
    try:
        if len(abstract.split()) < 50 or abstract == 'none':
            abstract = get_abstract_last(root, english_words)
    except:
        abstract = get_abstract_last(root, english_words)
    
    abstract = format_paragraph(abstract)
    
    article["Abstract"] = abstract


    return article

#********************************************** RUNABLE FUNCTION ****************************************************************************************************

def load(file, text):
    english_words = set(words.words())
    root = get_root(file)
    article = get_details(root, text, english_words)

    return article

# *******************************************************************************************************************************************************************
# ************************ EXECUTING EXTRACTION AND SAVING .JSON OUTPUT *********************************************************************************************
#********************************************************************************************************************************************************************
current_directory = os.path.dirname(os.path.abspath(__file__))
target_dir_xml = os.path.join(current_directory, "Outputs", "Xml")
target_dir_txt = os.path.join(current_directory, "Outputs", "Txt")

articles = []
not_work = []
for filename in os.listdir(target_dir_xml):
    xml_file = os.path.join(target_dir_xml, filename)
    txt_file = os.path.join(target_dir_txt, filename.replace(".cermxml", ".cermtxt"))
    filename_pdf = filename.replace(".cermxml", ".pdf")

    print("Processing file:", filename_pdf)
    try: 
        article = load(xml_file, txt_file)
        articles.append(article)
    except Exception as e:
        print(f"Error with file {filename_pdf}: {e}")
        not_work.append(filename_pdf)

# Print summary
print(f"Number of processed articles: {len(articles)}")
print(f"Number of files that failed to process: {len(not_work)}")
print(f"Files not processed:")
for files in not_work:
    print(files)

# Convert the list of dictionaries to a JSON string
json_string = json.dumps(articles, indent=4)

# Optionally, save the JSON string to a file
with open("./Outputs/Extract/articles.json", "w") as file:
    file.write(json_string)

print("Saved Complete")





