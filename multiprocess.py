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

from utils import writeMessageTxt, readCSV, dropExistCombinations

def mpCrawler(ERROR_TXT_PATH, FILE_PATH, authorCombinations, searchError):
    # 去除在以下兩個檔案中的combinations 
    # coAuthor/distribution/subProcess/error.txt
    # coAuthor/distribution/subProcess/coAuthor.csv
    authorCombinations = dropExistCombinations(FILE_PATH, ERROR_TXT_PATH, authorCombinations, searchError)

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

        # AU-ID(55701833100) AND AU-ID(56422845100)

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
            writeMessageTxt(ERROR_TXT_PATH, f"{authorCombination[0].authorID}!@!{authorCombination[1].authorID}")
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
            originalCoAuthorDF = readCSV(FILE_PATH)
            df = pd.DataFrame(resultBuffer)
            print(df)

            if originalCoAuthorDF is not None: # 若舊的存在，則合併舊檔案
                newDF = pd.concat([originalCoAuthorDF, df], axis=0, ignore_index=True)
                newDF.to_csv(FILE_PATH, index=False, encoding='UTF-8')
            else:
                df.to_csv(FILE_PATH, index=False, encoding="UTF-8")

            # reset resultBuffer
            resultBuffer = {
                'AuthorName1': [],
                'AuthorID1': [],
                'AuthorName2': [],
                'AuthorID2': [],
                'Num': []
            }

    driver.quit()




def mpCrawlerViaAPI(ERROR_TXT_PATH, FILE_PATH, authorCombinations, searchError):
    # 去除在以下兩個檔案中的combinations 
    # coAuthor/distribution/subProcess/error.txt
    # coAuthor/distribution/subProcess/coAuthor.csv
    # authorCombinations = dropExistCombinations(FILE_PATH, ERROR_TXT_PATH, authorCombinations, searchError)

    API_KEY = '25061a869d59f33bcd8df63aea742de1'
    API_URL = 'https://api.elsevier.com/content/search/scopus'

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

        params = {
            'query': f"AU-ID({authorCombination[0].authorID}) AND AU-ID({authorCombination[1].authorID})",
            'apiKey': API_KEY
        }

        retv =requests.get(API_URL, params=params)

        print(retv)
        exit(0)

        resultBuffer['AuthorName1'].append(authorCombination[0].originalName)
        resultBuffer['AuthorID1'].append(authorCombination[0].authorID)
        resultBuffer['AuthorName2'].append(authorCombination[1].originalName)
        resultBuffer['AuthorID2'].append(authorCombination[1].authorID)
        resultBuffer['Num'].append(coArticleCount)
        ct+=1

        if ct%100==0:
            originalCoAuthorDF = readCSV(FILE_PATH)
            df = pd.DataFrame(resultBuffer)
            print(df)

            if originalCoAuthorDF is not None: # 若舊的存在，則合併舊檔案
                newDF = pd.concat([originalCoAuthorDF, df], axis=0, ignore_index=True)
                newDF.to_csv(FILE_PATH, index=False, encoding='UTF-8')
            else:
                df.to_csv(FILE_PATH, index=False, encoding="UTF-8")

            # reset resultBuffer
            resultBuffer = {
                'AuthorName1': [],
                'AuthorID1': [],
                'AuthorName2': [],
                'AuthorID2': [],
                'Num': []
            }

    driver.quit()