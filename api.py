from flask import Flask, request, jsonify
import os
from tempfile import NamedTemporaryFile
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import re
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))
from llama_index.core import SimpleDirectoryReader
import os
from scipy.spatial.distance import cosine   
import fitz
from docx import Document
import glob
from sklearn.metrics.pairwise import cosine_similarity
import torch
import pandas as pd
from transformers import BertTokenizer, BertModel
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained("bert-base-uncased")

app = Flask(__name__)

def get_file_path_by_name(file_name):
    file_path = None
    for path in glob.glob(f'**/{file_name}', recursive=True):
        if file_name in path:
            file_path = path
            break
        file_path = os.path.abspath(file_path)
    return file_path


def preprocessing(document):
    """Preprocesses text data.

    Args:
        document: A list containing the text data.

    Returns:
        The preprocessed text as a string.
    """

    text1 = document[0].text.replace('\n', '').lower()
    text = re.sub(r'[^\x00-\x7F]+', '', text1)  # Remove non-ASCII characters
    tokens = word_tokenize(text)
    tokens = [re.sub(r'[^a-zA-Z\s]', '', token) for token in tokens]  # Remove punctuation
    tokens = [token for token in tokens if token]  # Remove empty tokens
    filtered_tokens = [token for token in tokens if token not in stop_words]  # Remove stopwords
    preprocessed_text = ' '.join(filtered_tokens)
    return preprocessed_text

def embedding_model(data):
    """Encodes data using the provided model.

    Args:
        data: The text data to encode.

    Returns:
        The encoded representation of the data.
    """
    encoded_input = tokenizer(data, return_tensors='pt',max_length=512,truncation=True)
    with torch.no_grad():
        output = model(**encoded_input)
    # text_embedding = model.encode(output)
    return output

def jd_embedding(uploaded_jd_file):
    """Computes the embedding for a job description (JD) file.

    Args:
        file: The path to the JD file.

    Returns:
        The embedding of the JD.
    """
    # # filepath=get_file_path_by_name(uploaded_jd_file)
    # print('filepath_jd_embedding',uploaded_jd_file)
    # document = SimpleDirectoryReader(input_files=[uploaded_jd_file]).load_data()
    # print('yes its started')
    # # document = file_reader(uploaded_jd_file)
    # print('yes')
    # data1 = preprocessing(document)
    # print('yes')
    # JD_embedding = embedding_model(data1)
    print(uploaded_jd_file)
    with open(uploaded_jd_file, 'rb') as uploaded_jd_file:
        with NamedTemporaryFile(delete=False) as tmp_file:
            tmp_filename = tmp_file.name
            tmp_file.write(uploaded_jd_file.read())
    document = SimpleDirectoryReader(input_files=[tmp_filename]).load_data()
    data = preprocessing(document)
    JD_embedding = embedding_model(data)
    os.unlink(tmp_filename)  # Delete temporary file
    return JD_embedding

def RESUME_embedding(folder):
    """Computes the embedding for each resume in a folder.

    Args:
        folder: The path to the folder containing resumes.

    Returns:
        A dictionary mapping filenames to their corresponding embeddings.
    """
    # print('oooooooooo',folder)
    resume_embeddings = {}
    for filename in folder:
        # if os.path.isfile(os.path.join(folder, filename)):
            # filepath=get_file_path_by_name(filename)
            print('llllllllllllllllllllllll',filename)
            # filepath = os.path.join(folder, filename)
            document = SimpleDirectoryReader(input_files=[filename]).load_data()
            # document = file_reader(filename)
            REsume_embedding = embedding_model(preprocessing(document))
            resume_embeddings[filename] = REsume_embedding
    return resume_embeddings


# @app.route('/score_resumes', methods=['POST'])
def scoring(folder,file):
    
    """Scores resumes in a folder based on their similarity to a job description (JD).

    Args:
        folder: The path to the folder containing resumes.
        file: The path to the JD file.

    Prints:
        A sorted dictionary of filenames and their similarity scores to the JD (descending order).
    """
    JD_embedding = jd_embedding(file)
    REsume_embedding = RESUME_embedding(folder)
    score_dict = {}

    for filename, resume_embedding in REsume_embedding.items():
        # print()
        # resume_embedding = RESUME_embedding(filename)
        cosine_JD=cosine_similarity(JD_embedding['pooler_output'], resume_embedding['pooler_output'])
        print('cosine',cosine_JD)
        similarity_score_percentage = cosine_JD[0][0] * 100
        score_dict[os.path.basename(filename)] = similarity_score_percentage

    sorted_dict_desc = dict(sorted(score_dict.items(), key=lambda item: item[1], reverse=True))
    df = pd.DataFrame(list(sorted_dict_desc.items()), columns=['Resume', 'Score'])
    print('ff',df)
    return df.to_dict(orient='records')
    # return df

@app.route('/score_resume', methods=['POST'])
def score_resumes():
    JD_folder_path = r'D:/jdcv_score_app/jdcv_score_app/temp1/'
    resume_folder_path = r'D:/jdcv_score_app/jdcv_score_app/temp2/'

    if 'jd_file' not in request.files or 'resumes' not in request.files:
        return jsonify({'error': 'Please provide a JD file and at least one resume file.'}), 400
    
    jd_file = request.files['jd_file']
    resumes = request.files.getlist('resumes')

    print('jd file',jd_file)
    os.makedirs(JD_folder_path,exist_ok=True)
    os.makedirs(resume_folder_path,exist_ok=True)

    # Save the uploaded files temporarily or handle them as required
    # Example: Save the JD file

    jd_file_path =  os.path.join(JD_folder_path, jd_file.filename)
    jd_file.save(jd_file_path)
    print('jd_api_filepath',jd_file_path)
    
    # Example: Save resumes
    resume_paths = []
    for resume in resumes:
        resume_path = os.path.join(resume_folder_path, resume.filename)
        resume.save(resume_path)
        resume_paths.append(resume_path)
    print('resumepaths',resume_paths)
    
    # Calculate scores
    sorted_scores = scoring(resume_paths,jd_file_path)
    # Remove temporary files if necessary
    
    return jsonify(sorted_scores), 200

if __name__ == '__main__':
    app.run(debug=True,port=5001)
