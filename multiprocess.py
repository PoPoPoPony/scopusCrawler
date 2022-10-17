from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm
import re
import pandas as pd
import os
from time import sleep
import requests
from author import Author

from utils import writeMessageTxt, readCSV, dropExistCombinations, saveData

def mpCrawler(ERROR_TXT_PATH, FILE_PATH, authorCombinations, searchError):
    # 去除在以下兩個檔案中的combinations 
    # coAuthor/distribution/subProcess/error.txt
    # coAuthor/distribution/subProcess/coAuthor.csv
    authorCombinations = dropExistCombinations(FILE_PATH, ERROR_TXT_PATH, authorCombinations, searchError)
    authorCombinations = authorCombinations.tolist()
    for i in range(len(authorCombinations)):
        authorNameAndID = authorCombinations[i].split("@!@")

        author1Name, author1ID = authorNameAndID[0].split("!@!")
        author1 = Author(authorID=author1ID, originalName=author1Name)
        author2Name, author2ID = authorNameAndID[1].split("!@!")
        author2 = Author(authorID=author2ID, originalName=author2Name)

        authorCombinations[i] = [author1, author2]


    options=webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')

    searchPageBaseUrl = "https://www.scopus.com/search/form.uri?display=advanced&s="
    driver = webdriver.Chrome(options=options)
    # driver.maximize_window()

    ct = 0
    resultBuffer = {
        'AuthorName1': [],
        'AuthorID1': [],
        'AuthorName2': [],
        'AuthorID2': [],
        'Num': []
    }

    for authorCombination in tqdm(authorCombinations):
        print(f" author1 : {authorCombination[0].originalName}, author2 : {authorCombination[1].originalName}")
        url = f"{searchPageBaseUrl}"
        driver.get(url)

        inputElem = driver.find_element(By.XPATH, '//*[@id="searchfield"]')
        inputElem.clear()
        inputElem.send_keys(f"AU-ID({authorCombination[0].authorID}) AND AU-ID({authorCombination[1].authorID})")

        searchBtn = driver.find_element(By.XPATH, '//*[@id="advSearch"]')
        searchBtn.click()

        try:
            WebDriverWait(driver,2,0.1).until(
            # 條件：直到元素載入完成
                EC.presence_of_element_located((By.XPATH, '//*[@id="searchResFormId"]'))
            )
        except:
            writeMessageTxt(ERROR_TXT_PATH, f"{authorCombination[0].originalName}!@!{authorCombination[0].authorID}@!@{authorCombination[1].originalName}!@!{authorCombination[1].authorID}")
            print("documentHeader not found!")
            continue

        # 如果找不到數字的話，當作沒有合著文章
        try:
            coArticleCount = driver.find_element(By.XPATH, '//*[@id="searchResFormId"]/div[1]/div/header/h1/span[1]').get_attribute("textContent")
            coArticleCount = re.sub(u"([^\u0030-\u0039])", "", coArticleCount)
        except:
            coArticleCount = '0'

        resultBuffer['AuthorName1'].append(authorCombination[0].originalName)
        resultBuffer['AuthorID1'].append(authorCombination[0].authorID)
        resultBuffer['AuthorName2'].append(authorCombination[1].originalName)
        resultBuffer['AuthorID2'].append(authorCombination[1].authorID)
        resultBuffer['Num'].append(coArticleCount)
        ct+=1

        if ct%100==0:
            saveData(resultBuffer, FILE_PATH)

            # reset resultBuffer
            resultBuffer = {
                'AuthorName1': [],
                'AuthorID1': [],
                'AuthorName2': [],
                'AuthorID2': [],
                'Num': []
            }
    saveData(resultBuffer, FILE_PATH)
    driver.quit()


def mpCrawlerViaAPI(ERROR_TXT_PATH, FILE_PATH, authorCombinations, searchError, ALL_API_KEYS):
    # 去除在以下兩個檔案中的combinations 
    # coAuthor/distribution/subProcess/error.txt
    # coAuthor/distribution/subProcess/coAuthor.csv
    authorCombinations = dropExistCombinations(FILE_PATH, ERROR_TXT_PATH, authorCombinations, searchError)

    authorCombinations = authorCombinations.tolist()
    for i in range(len(authorCombinations)):
        authorNameAndID = authorCombinations[i].split("@!@")

        author1Name, author1ID = authorNameAndID[0].split("!@!")
        author1 = Author(authorID=author1ID, originalName=author1Name)
        author2Name, author2ID = authorNameAndID[1].split("!@!")
        author2 = Author(authorID=author2ID, originalName=author2Name)

        authorCombinations[i] = [author1, author2]

    API_URL = 'https://api.elsevier.com/content/search/scopus'

    ct = 0
    resultBuffer = {
        'AuthorName1': [],
        'AuthorID1': [],
        'AuthorName2': [],
        'AuthorID2': [],
        'Num': []
    }
    dropCurrentAPI = False
    API_KEY_IDX = 0

    for authorCombination in tqdm(authorCombinations):
        print(f" author1 : {authorCombination[0].originalName}, author2 : {authorCombination[1].originalName}")

        API_KEY = ALL_API_KEYS[API_KEY_IDX]
        params = {
            'query': f"AU-ID({authorCombination[0].authorID}) AND AU-ID({authorCombination[1].authorID})",
            'apiKey': API_KEY 
        }

        retv=requests.get(API_URL, params=params)

        try:
            coArticleCount = retv.json()['search-results']['opensearch:totalResults']
            if retv.headers['X-ELS-Status']!='OK':
                raise Exception("Quote exceed!")
        except:
            writeMessageTxt(ERROR_TXT_PATH, f"{authorCombination[0].originalName}!@!{authorCombination[0].authorID}@!@{authorCombination[1].originalName}!@!{authorCombination[1].authorID}")
            print("coArticleCount not found!")

            API_KEY_IDX+=1
            if API_KEY_IDX<=len(ALL_API_KEYS): # 判斷還有沒有API_KEY可以使用
                continue
            else:
                break

        resultBuffer['AuthorName1'].append(authorCombination[0].originalName)
        resultBuffer['AuthorID1'].append(authorCombination[0].authorID)
        resultBuffer['AuthorName2'].append(authorCombination[1].originalName)
        resultBuffer['AuthorID2'].append(authorCombination[1].authorID)
        resultBuffer['Num'].append(coArticleCount)

        ct+=1
        if ct%100==0:
            saveData(resultBuffer, FILE_PATH)
            # reset resultBuffer
            resultBuffer = {
                'AuthorName1': [],
                'AuthorID1': [],
                'AuthorName2': [],
                'AuthorID2': [],
                'Num': []
            }

    saveData(resultBuffer, FILE_PATH)
