from utils import readCSV, dropExistCombinations, collectSubFoldersData
from multiprocess import mpCrawler
import numpy as np
from author import Author
import argparse
import os
from tqdm import tqdm
import multiprocessing
import glob
import pandas as pd
import shutil


# 從domain.csv中的作者ID尋找合著數量
if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--searchError', '-e', action="store_true", help='search DOI in error txt (in the distribution)')
    parser.add_argument('--distributionOrder', '-d', type=int, required=True, help='select which distribution to work on')
    parser.add_argument('--mpNum', '-m', type=int, default=multiprocessing.cpu_count(), help='multiprocess num')
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
        for line in lines:
            authorName1, authorID1, authorName2, authorID2 = line.split('!@!')
            author1 = Author(originalName=authorName1, authorID=str(authorID1))
            author2 = Author(originalName=authorName2, authorID=str(authorID2))
            authorCombinations.append([author1, author2])

    # 去除在以下兩個檔案中的combinations 
    # coAuthor/distribution/error.txt
    # coAuthor/distribution/coAuthor.csv
    authorCombinations = dropExistCombinations(FILE_PATH, ERROR_TXT_PATH, authorCombinations, args.searchError)
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

