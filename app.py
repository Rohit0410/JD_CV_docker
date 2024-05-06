import pprint
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader,ServiceContext
import docx2txt
import os
from statistics import mean
import re
from fastapi import FastAPI, HTTPException
from typing import List
from flask import Flask, jsonify,request, json
api_key = "AIzaSyCOiUIr-5sqiGvxrEtH29gtcxfF672JFDc"
import google.generativeai as genai
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

app = Flask(__name__)

def JD(jd):
    document_JD=SimpleDirectoryReader(input_files=[jd]).load_data()
    print(document_JD)
    Document_JD=""" """
    for i in document_JD:
        Document_JD+=i.text.replace('\n','').replace('\t','')
    prompt_prefix_JD="""you are an HR executive. you have this Job Description"""
    prompt_JD=Document_JD
    prompt_suffix_JD =["get the key skills required for this position","get me years of experience required for this position. just get the year in numeric","get me all the details about the experience must the candidate should have for this position"]
    key_skills_JD=model.generate_content(prompt_prefix_JD+prompt_JD+prompt_suffix_JD[0]).text.replace('\n','')
    years_experience_JD=model.generate_content(prompt_prefix_JD+prompt_JD+prompt_suffix_JD[1]).text.replace('\n','')
    professional_experience_JD=model.generate_content(prompt_prefix_JD+prompt_JD+prompt_suffix_JD[2]).text.replace('\n','')
    return key_skills_JD,years_experience_JD,professional_experience_JD

def RESUME(folder):
    # folder=r"D:\Rohit\jdcv_score_app\jdcv_score_app\MANUAL DATA\mixed OPPO INDIA"
    print(folder)
    global resume_section
    resume_section={}
    # for i in os.listdir(folder):
    for i in folder:
        section=[]
        # filepath=os.path.join(folder,i)
        print(i)
        document_Resume=SimpleDirectoryReader(input_files=[i]).load_data()
        Document_Resume=""""""
        for j in document_Resume:
            Document_Resume+=j.text
        prompt_prefix_Resume="""you are an HR executive. your job is to get some details from this Resume """
        prompt_Resume=Document_Resume
        prompt_suffix_Resume =["get me all the skills of this candidate from the resume","get me the years of experience the candidate have in total like 15 years, 1year.","get me the summary of the professional experiences from the resume"]
        key_skills_Resume=model.generate_content(prompt_prefix_Resume+prompt_Resume+prompt_suffix_Resume[0]).text.replace('\n','')
        years_experience_Resume=model.generate_content(prompt_prefix_Resume+prompt_Resume+prompt_suffix_Resume[1]).text.replace('\n','')
        professional_experience_Resume=model.generate_content(prompt_prefix_Resume+prompt_Resume+prompt_suffix_Resume[2]).text.replace('\n','')
        section.append(key_skills_Resume)
        section.append(years_experience_Resume)
        section.append(professional_experience_Resume)
        # resume_section[i]=[str(key_skills_Resume),str(years_experience_Resume),str(professional_experience_Resume)]
        resume_section[i]=section
    return resume_section


def compare(file,folder):
    jd = JD(file)
    resume = RESUME(folder)
    print(type(resume))
    print(resume)
    keys=list(resume.keys())
    h={}
    for i in keys:
        print(i)
        y=resume[i]
        
        prompt_skills="""You are an HR Executive tasked with scoring the similarity between the skills required in a job description (JD) and the skills listed on a resume. Below are the skills from both:
        Skills in the JD: {}
        Skills in the Resume: {}
        Calculate the similarity between these two sets of skills and provide the score in percentage form. Ensure the score is expressed as a plain number (e.g., 100, 50, 0) without any additional text like "Similarity Score:" or "%".""".format(jd[0],y[0])
        
        prompt_year="""You are an HR Executive required to evaluate the similarity in years of experience between what is specified in a job description and what is detailed on a resume. The details are as follows:
        Years of experience required in the JD: {}
        Years of experience listed on the Resume: {}
        Calculate the similarity between the two values and provide the score as a plain percentage number (e.g., 10, 0, 19) without using any additional text like "Similarity Score:" or "%".""".format(jd[1],y[1])
        
        prompt_profession="""You are an HR Executive tasked with scoring the similarity of professional experience as described in a job description (JD) and as listed on a resume. Here are the details:
        Professional experience in the JD: {}
        Professional experience on the Resume: {}
        Assess the similarity between the professional experiences listed in the JD and the resume. Provide the similarity score in a plain percentage number (e.g., 25, 10, 0), ensuring you do not include additional text like "Similarity Score:" or "%" next to the number.""".format(jd[2],y[2])
        
        skills_compare=model.generate_content(prompt_skills).text.replace('\n','')
        year_compare=model.generate_content(prompt_year).text.replace('\n','')
        profession_compare=model.generate_content(prompt_profession).text.replace('\n','')

        match1 = re.search(r'\d+', skills_compare)
        match2 = re.search(r'\d+', year_compare)
        match3 = re.search(r'\d+', profession_compare)
        if match1:
            l1=int(match1.group(0))
        else:
            l1=0
        
        if match2:
            l2=int(match2.group(0))
        else:
            l2=0
        
        if match3:
            l3=int(match3.group(0))
        else:
            l3=0
        print(l1,l2,l3)

        print('h',h)

        h[i]=mean([int(l1),int(l2),int(l3)])
        # h[i]=mean([int(float(skills_compare)),int(float(year_compare)),int(float(profession_compare))])
        h=dict(sorted(h.items(), key=lambda item: item[1], reverse=True))
    print(h)
    return h

# compare(r"D:\Rohit\drive-download-20240320T071743Z-001\Oppo India- Chief Financial Officer\mixed\jd4.docx",r"D:\Rohit\jdcv_score_app\jdcv_score_app\MANUAL DATA\mixed OPPO INDIA")

@app.route('/score_resumes', methods=['POST'])
def scoring():
    JD_folder_path = r'D:/jdcv_score_app/jdcv_score_app/temp3/'
    resume_folder_path = r'D:/jdcv_score_app/jdcv_score_app/temp4/'

    if 'jd_file' not in request.files or 'resumes' not in request.files:
        return jsonify({'error': 'Please provide a JD file and at least one resume file.'}), 400
    
    jd_file = request.files['jd_file']
    resumes = request.files.getlist('resumes')

    print(';;;;;',jd_file)
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

    score = compare(jd_file_path,resume_paths)
    return jsonify(score), 200

if __name__ == '__main__':
    app.run(debug=True)



