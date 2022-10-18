from utils import readCSV, dropExistCombinations, collectSubFoldersData
from multiprocess import mpCrawler, mpCrawlerViaAPI
import numpy as np
from author import Author
import argparse
import os
from tqdm import tqdm
import multiprocessing
import glob
import pandas as pd
import shutil
import requests
import json


# 從domain.csv中的作者ID尋找合著數量
if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--searchError', '-e', action="store_true", help='search DOI in error txt (in the distribution)')
    parser.add_argument('--distributionOrder', '-d', type=int, required=True, help='select which distribution to work on')
    parser.add_argument('--mpNum', '-m', type=int, default=multiprocessing.cpu_count(), help='multiprocess num')
    parser.add_argument('--webCrawler', '-w', action="store_true", help='use WebCrawler to get data(default use API)')
    args = parser.parse_args()

    distributionOrder = args.distributionOrder
    distributionFolder = f'coAuthor/distribution{distributionOrder}'
    COMBINATIONS_FILE_PATH = f'{distributionFolder}/combinations.txt'
    ERROR_TXT_PATH = f'{distributionFolder}/error.txt'
    FILE_PATH = f'{distributionFolder}/coAuthor.csv'

    collectSubFoldersData(ROOT_FILE_PATH=distributionFolder) # 收集所有distribution的資料

    # 刪除所有的distribution
    folderNames = glob.glob(f"{distributionFolder}/subProcess*")
    for folderName in folderNames:
        shutil.rmtree(folderName)

    authorCombinations = []
    with open(COMBINATIONS_FILE_PATH, mode='r', encoding="UTF-8") as f:
        lines = f.readlines()
        lines = [x[:-1] for x in lines] # 去除換行符號
        authorCombinations.extend(lines)

    # 去除在以下兩個檔案中的combinations 
    # coAuthor/distribution/error.txt
    # coAuthor/distribution/coAuthor.csv
    authorCombinations = dropExistCombinations(FILE_PATH, ERROR_TXT_PATH, authorCombinations, args.searchError)
    
    if args.webCrawler:
        authorCombinationsSets = np.array_split(authorCombinations, args.mpNum)
        process_lst = []
        manager = multiprocessing.Manager()
        for i in range(args.mpNum):
            SUB_PROCESS_FOLDER = f'{distributionFolder}/subProcess{i}'
            if not os.path.exists(SUB_PROCESS_FOLDER):
                os.mkdir(SUB_PROCESS_FOLDER)
            SUB_PROCESS_ERROR_TXT_PATH = f'{SUB_PROCESS_FOLDER}/error.txt'
            SUB_PROCESS_FILE_PATH = f'{SUB_PROCESS_FOLDER}/coAuthor.csv'
            p = multiprocessing.Process(target=mpCrawler, args=(SUB_PROCESS_ERROR_TXT_PATH, SUB_PROCESS_FILE_PATH, authorCombinationsSets[i], args.searchError))
            process_lst.append(p)
            p.start()

        for i in range(args.mpNum):
            process_lst[i].join()
    else:

        url = "https://script.google.com/macros/s/AKfycbz-xUKmN2GIfygrpkR57crj9U5MnaVlpFFay7f6RWbaVoT3iXwyUAG4RuxDW2x0RgWQ/exec"
        retv = requests.get(url, params={'mode': 'read', 'sheetName': 'API'}).json()
        ALL_API_KEYS = [x[0] for x in retv if x[1]=='OK']

        authorCombinationsSets = np.array_split(authorCombinations, args.mpNum)
        process_lst = []
        manager = multiprocessing.Manager()
        exceedAPIs = manager.list()
        for i in range(args.mpNum):
            SUB_PROCESS_FOLDER = f'{distributionFolder}/subProcess{i}'
            if not os.path.exists(SUB_PROCESS_FOLDER):
                os.mkdir(SUB_PROCESS_FOLDER)
            SUB_PROCESS_ERROR_TXT_PATH = f'{SUB_PROCESS_FOLDER}/error.txt'
            SUB_PROCESS_FILE_PATH = f'{SUB_PROCESS_FOLDER}/coAuthor.csv'
            p = multiprocessing.Process(target=mpCrawlerViaAPI, args=(
                SUB_PROCESS_ERROR_TXT_PATH, SUB_PROCESS_FILE_PATH, authorCombinationsSets[i], args.searchError, ALL_API_KEYS, i, exceedAPIs))
            process_lst.append(p)
            p.start()

        for i in range(args.mpNum):
            process_lst[i].join()

        data = retv
        for d in data:
            if d[0] in exceedAPIs:
                d[1] = 'exceed'
        data = json.dumps(data)
        requests.get(url, params={'mode': 'write', 'sheetName': 'API', 'data': data})
