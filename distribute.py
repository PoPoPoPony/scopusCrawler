from selenium import webdriver
from time import sleep
import csv
from utils import namePreProcess, getDomainNums, getDomainDF, readCSV, writeMessageTxt, concatDF, dropExistCombinations, collectSubFoldersData
import numpy as np
from author import Author
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import argparse
import os
from tqdm import tqdm
import itertools
import shutil
import glob

# 從domain.csv中的作者ID尋找合著數量
if __name__ == '__main__':
    DOMAIN_FILE_PATH = 'domainFromDOI/domain.csv'
    ERROR_TXT_PATH = 'coAuthor/error.txt'
    FILE_PATH = 'coAuthor/coAuthor.csv'

    parser = argparse.ArgumentParser()
    parser.add_argument('--searchError', '-e', action="store_true", help='search error combinations in error txt')
    parser.add_argument('--distributionNum', '-n', type=int, required=True, help='distrubute combinations to N subset')
    args = parser.parse_args()

    collectSubFoldersData(ROOT_FILE_PATH='coAuthor') # 收集所有distribution的資料

    # 刪除所有的distribution
    folderNames = glob.glob("coAuthor/distribution*")
    for folderName in folderNames:
        shutil.rmtree(folderName)

    # 從CSV讀取所有要處理的名字、authorID
    authors = [] # 儲存所有author
    domainDF = readCSV(DOMAIN_FILE_PATH)
    domainDF = domainDF.iloc[:, :2].drop_duplicates().reset_index(drop=True) # 只取名字跟authorID
    originalNames = domainDF['OriginalName'].to_list()
    authorIDs = [str(x) for x in domainDF['AuthorID'].to_list()]
    for i in range(len(originalNames)):
        author = Author(originalName=originalNames[i], authorID=authorIDs[i])
        authors.append(author)

    authorCombinations = []
    for subset in itertools.combinations(authors, 2):
        authorCombinations.append(subset)

    # 去除在以下兩個檔案中的combinations 
    # coAuthor/error.txt
    # coAuthor/coAuthor.csv
    authorCombinations = dropExistCombinations(FILE_PATH, ERROR_TXT_PATH, authorCombinations, args.searchError)
    authorCombinationsSets = np.array_split(authorCombinations, args.distributionNum)

    print("distribute start!")
    for i in tqdm(range(len(authorCombinationsSets))):
        data = []
        subsetPath = f'coAuthor/distribution{i}'
        os.mkdir(subsetPath)

        for authorCombination in authorCombinationsSets[i]:
            data.append(f"{authorCombination[0].originalName}!@!{authorCombination[0].authorID}!@!{authorCombination[1].originalName}!@!{authorCombination[1].authorID}\n")
        
        # write file
        filePath = f'coAuthor/distribution{i}/combinations.txt'
        with open(filePath, mode='a', encoding='UTF-8') as f:
            f.writelines(data)
    print("distribute complete!")