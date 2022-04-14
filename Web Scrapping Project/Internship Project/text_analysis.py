# -*- coding: utf-8 -*-
"""
Created on Mon Apr 11 15:56:55 2022

@author: Shivam Shrivastava
"""
#Importing Libraries
import pandas as pd
from nltk.tokenize import word_tokenize
import string
import re
import time
import nltk.data 

tokenizer = nltk.data.load('tokenizers/punkt/english.pickle') #Tokenize the paragraphs into sentences

start = time.perf_counter()

#Function to count the syllable of the words
def syllable_count(word):
    word = word.lower()
    count = 0
    vowels = "aeiouy"
    if word[0] in vowels:
        count += 1
    for index in range(1, len(word)):
        if word[index] in vowels and word[index - 1] not in vowels:
            count += 1
    if word.endswith("e"):
        count -= 1
    if count == 0:
        count += 1
    return count

#Function to perform text analysis and save the required parameter as per "Output Data Structures.xlsx"
def text_analysis(urlId, textFile, df, stopwords, output_df):
    filename = textFile
    file  = open(filename, "r", encoding = 'utf-8')
    f = file.read()
    #1- Sentiment Analysis
    #1.1 and 1.3 - Cleaning using stopwords list and tokenize the text using nltk library
    clean_text = [word for word in word_tokenize(f) if word not in stopwords]
    clean_text = [word.upper() for word in clean_text if word not in string.punctuation]

    #1.2 - Creating dictionary of Positive and Negative words
    word_dict = {}
    for word in clean_text:
        if word in list(df['Word']):
            if df[df['Word']==word]['Positive'].values[0]>0:
                word_dict[word] = 'Positive'
            elif df[df['Word']==word]['Negative'].values[0]>0:
                word_dict[word] = 'Negative'
            else:
                word_dict[word] = 'Neutral'

    #Positive Score
    positive = [key for key, value in word_dict.items() if value == 'Positive']
    negative = [key for key, value in word_dict.items() if value == 'Negative']
    pos_num, neg_num = len(positive), -len(negative)

    #Polarity Score, Subjective Score
    polarity_score = (pos_num - neg_num )/((pos_num  + neg_num) + 0.000001)
    clean_text_len = len(clean_text)
    subjective_score = (pos_num + neg_num )/ ((clean_text_len) + 0.000001)
    
    #2- Analysis of Readability

    #Average Sentence Length
    sent_num = len(tokenizer.tokenize(f)) #no. of sentences
    avg_sen_len = clean_text_len/sent_num

    #Percentage of Complex words and Fog Index
    complex_word_num = 0
    for word in clean_text:
        if syllable_count(word)>2:
            complex_word_num+=1 #4 Complex Word Count
    complex_word_percentage = complex_word_num / clean_text_len
    fog_index = 0.4 * (avg_sen_len + complex_word_percentage)
    
    #3- Average Number of Words Per Sentence
    no_of_words = len(word_tokenize(f))
    avg_no_of_words_per_sen = no_of_words/sent_num

    #5- Word Count
    word_count = clean_text_len

    #6- Syllable Count Per Word
    no_of_syllable = 0
    for word in clean_text:
        no_of_syllable += syllable_count(word)
    syllable_per_word = no_of_syllable/clean_text_len

    #7- Personal Pronouns Count
    pronouns_count = 0
    prons = ["I", "we", "my", "ours", "us"]
    for word in prons:
        if re.search(r"\b" + re.escape(word) + r"\b", " ".join(word_tokenize(f))):
            pronouns_count+=1 

    #8- Average Word Length
    no_of_char = 0
    for word in clean_text:
        for char in word:
            no_of_char+=len(char)
    avg_word_len = no_of_char/clean_text_len

    #Creating Output DataFrame
    output_df.at[urlId-1, ["POSITIVE SCORE", "NEGATIVE SCORE", "POLARITY SCORE", "SUBJECTIVITY SCORE", "AVG SENTENCE LENGTH", "PERCENTAGE OF COMPLEX WORDS", "FOG INDEX", "AVG NUMBER OF WORDS PER SENTENCE", "COMPLEX WORD COUNT", "WORD COUNT", "SYLLABLE PER WORD", "PERSONAL PRONOUNS", "AVG WORD LENGTH"]] = pos_num, neg_num, polarity_score, subjective_score, avg_sen_len, complex_word_percentage, fog_index, avg_no_of_words_per_sen, complex_word_num, word_count, syllable_per_word, pronouns_count, avg_word_len
    file.close()

    return output_df

    


#Main Function
if __name__ == "__main__":
    #Required Variables
    masterDictionary, stopWordsList, templateOutput = "Loughran-McDonald_MasterDictionary_1993-2021.csv", "StopWords_GenericLong.txt", "Output Data Structure.xlsx"
    df = pd.read_csv(masterDictionary)
    df = df.loc[0:86531, ['Word', 'Negative', 'Positive']]
    stopwords = open(stopWordsList).read().split("\n")
    output_df = pd.read_excel(templateOutput, engine='openpyxl')

    print("Starting Text Analysis on all the text files...")
    for i in range(1,  171):
        textFile = f"{i}.txt"
        output_df = text_analysis(i, textFile, df, stopwords, output_df)
    #Converting output dataframe to csv file
    output_df.to_csv('output.csv')
    #Execution Time
    finish = time.perf_counter()
    print(f'Finished in {finish-start}')

