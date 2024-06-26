import os
import json
import torch
import pickle
import pandas as pd
from torch.utils.data import TensorDataset
import re
import csv
from utils.utils import clean_tweet

test_file_name = '/exalt_emotion_train.tsv'
# Get the current directory of the script
current_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current_directory)
# Construct the path to the JSON file
json_file_path = os.path.join('../data', 'emotionToId.json')

# Read the JSON file
with open(json_file_path, 'r') as file:
    emotionToNum = json.load(file)
numToEmotion = {number:label for label, number in emotionToNum.items()}

def getData(tokenizer,file_name, train=True):
    
    data=pd.read_csv(file_name,sep='\t')
    
    #data=data[data[1]!='27'] #Remove neutral labels
    #data=data[[len(label.split(','))==1 for label in data[1].tolist()]] #Remove mutil labels
    
    sents=[tokenizer(clean_tweet(sent.lower()),padding='max_length',truncation=True,max_length=128) for sent in data.iloc[:, 1].values.tolist()]
    sents_input_ids=torch.tensor([temp["input_ids"] for temp in sents])
    sents_attn_masks=torch.tensor([temp["attention_mask"] for temp in sents])
    if train:
        labels=torch.tensor([emotionToNum[label] for label in data.iloc[:, 2].values.tolist()])
        dataset=TensorDataset(sents_input_ids,sents_attn_masks,labels)
    else:
        dataset = TensorDataset(sents_input_ids, sents_attn_masks)
    
    return dataset

def getTrainData(tokenizer,bert_name,data_path):
    if not os.path.exists(data_path+ "/%s"%(bert_name.split('/')[-1])):
        os.makedirs( data_path+"/%s"%(bert_name.split('/')[-1]))
    
    feature_file = data_path+"/%s/train_features.pkl"%(bert_name.split('/')[-1])
    if os.path.exists(feature_file):
        train_dataset = pickle.load(open(feature_file, 'rb'))
    else:
        train_dataset = getData(tokenizer,data_path+'/exalt_emotion_train.tsv')
        with open(feature_file, 'wb') as w:
            pickle.dump(train_dataset, w)
    return train_dataset

def getDevData(tokenizer,bert_name,data_path):
    feature_file = data_path+"/%s/dev_features.pkl"%(bert_name.split('/')[-1])
    if os.path.exists(feature_file):
        dev_dataset = pickle.load(open(feature_file, 'rb'))
    else:
        dev_dataset = getData(tokenizer,data_path+'/exalt_emotion_dev_participants.tsv')
        with open(feature_file, 'wb') as w:
            pickle.dump(dev_dataset, w)
    return dev_dataset


def getTestData(tokenizer,bert_name,data_path, test_file_name=test_file_name):
    # feature_file = data_path+"/%s/test_features.pkl"%(bert_name.split('/')[-1])
    # if os.path.exists(feature_file):
    #     test_dataset = pickle.load(open(feature_file, 'rb'))
    test_dataset = getData(tokenizer,data_path+test_file_name, train=False)
    # with open(feature_file, 'wb') as w:
    #     pickle.dump(test_dataset, w)
    return test_dataset

def saveTestResults(test_data_input_directory, prediction_values, output_file_name, test_file_name=test_file_name):
    data = pd.read_csv(test_data_input_directory + test_file_name, sep='\t')
    #sentIds = data.iloc[:, 0].values.tolist()
    tsvfile = open(output_file_name, 'w', newline='')
    writer = csv.writer(tsvfile, delimiter='\t', lineterminator='\n')
    header_as_list = data.columns.tolist()
    header_as_list.append("Predicted_Labels")
    del header_as_list[1]
    writer.writerow(header_as_list)
    for i, predict_val in enumerate(prediction_values):
        row_as_list = data.iloc[i].values.tolist()
        row_as_list.append(numToEmotion[predict_val])
        del row_as_list[1]
        writer.writerow(row_as_list)