from selenium import webdriver
from time import sleep
import csv
from utils import namePreProcess, getDomainNums, getDomainDF, readCSV, writeMessageTxt, concatDF
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

# 找作者所有領域的文章數量(FROM DOI)

if __name__ == '__main__':
    ERROR_TXT_PATH = 'domainFromDOI/excel/error.txt'
    ALL_DOI_FILE_PATH = 'domainFromDOI/excel/commentary-doi.csv'
    EXIST_DOI_FILE_PATH = 'domainFromDOI/excel/existDOI.txt'
    FILE_PATH = 'domainFromDOI/excel/domain.csv'

    parser = argparse.ArgumentParser()
    parser.add_argument('--searchError', '-e', action="store_true", help='search DOI in error txt')
    args = parser.parse_args()

    # 排除在error.txt的DOI
    existDOIs = []
    if os.path.exists(ERROR_TXT_PATH):
        if args.searchError:# 若要搜尋error作者的話，就把error.txt清空，重新寫入錯誤的作者
            os.remove(ERROR_TXT_PATH)
        else: # 若不搜尋error的作者的話，就把error中的作者當作已經搜尋過的作者(只是為了排除搜尋而已)
            try:
                with open(ERROR_TXT_PATH, mode='r', encoding="UTF-8") as f:
                    lines = f.readlines()
                    existDOIs.extend([x[:-1] for x in lines]) # 去除換行符號
            except:
                print(f"Invalid char while reading error txt!")

    # 排除在existDOI中的DOI
    if os.path.exists(EXIST_DOI_FILE_PATH):
        try:
            with open(EXIST_DOI_FILE_PATH, mode='r', encoding="UTF-8") as f:
                lines = f.readlines()
                existDOIs.extend([x[:-1] for x in lines]) # 去除換行符號
        except:
            print(f"Invalid char while reading existDOI txt!")

    # 排除在domain.csv中查詢過的作者
    existAuthorIDs = []
    domainDF = readCSV(FILE_PATH) # 查詢過的作者的df
    if domainDF is not None:
        existAuthorIDs.extend([str(x) for x in domainDF['AuthorID'].drop_duplicates().to_list()])

    # store = [] # 避免遇到同個作者要重複處理
    # authors = [] # 儲存所有Author物件
    DOIs = [] # 儲存所有原始名字(未處理過的)

    # 從CSV讀取所有要處理的名字
    with open(ALL_DOI_FILE_PATH, mode='r', newline='', encoding="UTF-8") as f:
        rows = list(csv.reader(f, delimiter=','))[1:]
        for row in rows:
            row = [row[i] for i in [0] if row[i]]
            DOIs.extend(row)

    DOIs = [DOI for DOI in DOIs if DOI not in existDOIs]

    options=webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')

    searchPageBaseUrl = "https://www.scopus.com/search/form.uri?display=advanced&s="
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()

    # for author in tqdm(authors):
    authorIDs = []

    for DOI in tqdm(DOIs):
        error = False
        print(f" DOI : {DOI}")
        currentAuthors = [] # 這個DOI的authors
        url = f"{searchPageBaseUrl}DOI({DOI})"
        driver.get(url)

        inputElem = driver.find_element(By.XPATH, '//*[@id="searchfield"]')
        inputElem.clear()
        inputElem.send_keys(f"DOI({DOI})")

        searchBtn = driver.find_element(By.XPATH, '//*[@id="advSearch"]')
        searchBtn.click()

        try:
            articleURL = WebDriverWait(driver,5,0.1).until(
            # 條件：直到元素載入完成
                EC.presence_of_element_located((By.XPATH, '//*[@id="resultDataRow0"]/td[1]/a'))
            )

            driver.get(articleURL.get_attribute("href"))
        except:
            writeMessageTxt(ERROR_TXT_PATH, DOI)
            print(f"{DOI} not found!")
            error = True
            continue

        
        try:
            authorsUL = WebDriverWait(driver,5,0.1).until(
            # 條件：直到元素載入完成
                EC.presence_of_element_located((By.XPATH, '//*[@id="doc-details-page-container"]/article/div[2]/section/div[2]/div/ul'))
            )
        except:
            writeMessageTxt(ERROR_TXT_PATH, DOI)
            print("authorsUL not Found!")
            error = True
            continue

        authorBtns = authorsUL.find_elements(By.TAG_NAME, 'els-button')

        for i in range(len(authorBtns)):
            try:
                authorBtns[i] = WebDriverWait(driver,5,0.1).until(
                # 條件：直到元素載入完成
                    EC.element_to_be_clickable(authorBtns[i])
                )
            except:
                writeMessageTxt(ERROR_TXT_PATH, DOI)
                print("authorBtns not Found!")
                error = True
                break # 這個DOI要重新搜尋
            
            for _ in range(3):
                try:
                    authorBtns[i].click()
                    break
                except Exception as e:
                    pass
            else: # 沒有break代表噴錯
                writeMessageTxt(ERROR_TXT_PATH, DOI)
                print("authorsBtn can not click!")
                error = True
                break # 這個DOI要重新搜尋

            try:
                authorsInfo = WebDriverWait(driver,5,0.1).until(
                # 條件：直到元素載入完成
                    EC.presence_of_element_located((By.XPATH, f'//*[@id="doc-details-page-container"]/article/div[2]/section/div[2]/div/ul/li[{i+1}]/div/div/div/div/div/els-stack/els-stack[1]/div/els-stack/els-button[1]'))
                )
            except:
                writeMessageTxt(ERROR_TXT_PATH, DOI)
                print("authorsInfo not Found!")
                error = True
                break
            
            authorID = authorsInfo.get_attribute("href").split("=")[1].split("&")[0]
            authorOriginalName = driver.find_element(By.XPATH, f'//*[@id="doc-details-page-container"]/article/div[2]/section/div[2]/div/ul/li[{i+1}]/div/div/div/div/div/els-stack/els-stack[1]/els-stack/h1').get_attribute("textContent")
            
            if (authorID not in authorIDs) and (authorID not in existAuthorIDs):
                currentAuthors.append(Author(authorID=authorID, originalName=authorOriginalName))
                authorIDs.append(authorID)

            # 隨便點旁邊一下，關閉sideWindow
            location = authorBtns[i].location
            action = webdriver.common.action_chains.ActionChains(driver)
            action.move_to_element_with_offset(authorBtns[0], 5, 5)
            action.click()
            action.perform()

        for author in currentAuthors:
            driver.get(f"https://www.scopus.com/authid/detail.uri?authorId={author.authorID}#tab=topics")
            domainNums = getDomainNums(driver)

            for domain, num in domainNums.items():
                author.setDomain(domain, num)

            originalDomainDF = readCSV(FILE_PATH)
            df = getDomainDF(author) # 新的作者的df
            print(df)
            if originalDomainDF is not None: # 若舊的存在，則合併舊檔案
                newDF = pd.concat([originalDomainDF, df], axis=0, ignore_index=True)
                newDF.to_csv(FILE_PATH, index=False, encoding='UTF-8')
            else:
                df.to_csv(FILE_PATH, index=False, encoding="UTF-8")
        
        if not error:
            # 將查詢完的DOI紀錄起來
            writeMessageTxt(EXIST_DOI_FILE_PATH, DOI)

    driver.quit()
    newDF = concatDF()
    newDF.to_csv('domainFromDOI/domain.csv', encoding='UTF-8', index=False)


