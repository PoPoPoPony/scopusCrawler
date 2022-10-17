import pandas as pd
from author import Author
from copy import deepcopy
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import pandas as pd
import os
from tqdm import tqdm
import glob
from typing import List


def namePreProcess(fullName:str) -> Author:
    # originalName =  fullName
    name = fullName.split(" ")
    name = [x for x in name if "." not in x and x]
    for i in range(len(name)):
        if name[i][-1]==',':
            name[i]=name[i][:-1]
        # name[i] = name[i].replace('\xa0', '')
        # name[i] = name[i].replace('\xfc', 'ü')
        # name[i] = name[i].replace('\xe9', 'é')
        # name[i] = name[i].replace('\xe8', 'é')

    return name


def getTitleNums(driver):
    titleNums = {}

    # 獲取文獻標題、引用次數
    # 每頁10個title
    for i in range(1, 11):
        try:
            title=WebDriverWait(driver,5,0.1).until(
            # 條件：直到元素載入完成
                EC.presence_of_element_located((By.XPATH, f'//*[@id="scopus-author-profile-page-control-microui__documents-panel"]/els-stack/div/div[2]/div/els-results-layout/div[1]/ul/li[{i}]/div/div[1]/div[1]/h4/a'))
            )
            title = title.get_attribute("textContent")


            # 引用為0的情況
            numElem = driver.find_elements(By.XPATH, f'//*[@id="scopus-author-profile-page-control-microui__documents-panel"]/els-stack/div/div[2]/div/els-results-layout/div[1]/ul/li[{i}]/div/div[3]/els-info-field/div/div/span/span')

            if len(numElem)>0:
                num = numElem[0].get_attribute("textContent")
            else:
                # 引用不為0的情況
                numElem = driver.find_element(By.XPATH, f'//*[@id="scopus-author-profile-page-control-microui__documents-panel"]/els-stack/div/div[2]/div/els-results-layout/div[1]/ul/li[{i}]/div/div[3]/els-info-field/div/div/els-button/span/els-typography')
                num = numElem.get_attribute("textContent")

            titleNums[title] = num
        except:
            print("getTitleNums Falid !")
            break
        
    return titleNums


def getDomainNums(driver):
    domainNums = {}
    try:
        domainTable = WebDriverWait(driver,15,0.1).until(
        # 條件：直到元素載入完成
            EC.presence_of_element_located((By.XPATH, '//*[@id="TopicsTable-module__E667w"]/tbody'))
        )
    except:
        # 沒有主題的情況
        domainNums['None'] = '0'
        return domainNums
    
    tableTRs = domainTable.find_elements(By.TAG_NAME, 'tr')
    for tr in tableTRs:
        domain, num = tr.find_elements(By.TAG_NAME, 'td')[:2]

        domain = domain.find_element(By.TAG_NAME, 'span').get_attribute("textContent")
        num = num.find_element(By.TAG_NAME, 'span').get_attribute("textContent")

        domainNums[domain] = num

    return domainNums


def getAuthorDF(author:Author):
    originalNames = []
    firstNames = []
    lastNames = []
    titles = []
    nums = []

    for title, num in author.article.items():
        originalNames.append(author.originalName)
        firstNames.append(author.firstName)
        lastNames.append(author.lastName)
        titles.append(title)
        nums.append(num)

    df = pd.DataFrame(list(zip(originalNames, firstNames, lastNames, titles, nums)), columns = ["OriginalName", "FirstName", "LastName", "Title", "CiteNum"])

    return df


def getDomainDF(author:Author):
    # # originalNames = []
    # # firstNames = []
    # # lastNames = []
    # domains = []
    # nums = []
    # info = []

    # # main2沒有ID需再修改

    # for domain, num in author.domain.items():
    #     if author.originalName:

    #     originalNames.append(author.originalName)
    #     firstNames.append(author.firstName)
    #     lastNames.append(author.lastName)
    #     domains.append(domain)
    #     nums.append(num)

    info = []
    columns = []

    if author.originalName:
        info.append([author.originalName]*len(author.domain))
        columns.append("OriginalName")

    if author.authorID:
        info.append([author.authorID]*len(author.domain))
        columns.append("AuthorID")

    if author.firstName:
        info.append([author.firstName]*len(author.domain))
        columns.append("FirstName")

    if author.lastName:
        info.append([author.lastName]*len(author.domain))
        columns.append("LastName")

    if author.domain:
        domains = []
        nums = []
        for domain, num in author.domain.items():
            domains.append(domain)
            nums.append(num)

        info.append(domains)
        info.append(nums)

        columns.append("Domain")
        columns.append("Num")

    df = pd.DataFrame(list(zip(*info)), columns = columns)

    return df


def readCSV(filePath:str):
    try:
        df = pd.read_csv(filePath, encoding="UTF-8")
        return df
    except FileNotFoundError:
        print("CSV File Not Found!")
        return None


# 原本是傳入Author，main.py & main2.py需修改
def writeMessageTxt(filePath:str, msg:str):
    try:
        with open(filePath, mode='a', encoding='UTF-8') as f:
            f.writelines(f"{msg}\n")
    except:
        print(f"{msg} has invalid char!")


def concatDF(filePath1:str='domainFromDOI/google_excel/domain.csv', filePath2:str='domainFromDOI/excel/domain.csv'):
    try:
        df1 = pd.read_csv(filePath1, encoding="UTF-8")
        df2 = pd.read_csv(filePath2, encoding="UTF-8")
    except FileNotFoundError:
        print("domain.csv not Found!")

    newDF = pd.concat([df1, df2], axis=0, ignore_index=True)
    newDF = newDF.drop_duplicates().reset_index(drop=True)

    return newDF
    

def dropExistCombinations(FILE_PATH:str, ERROR_TXT_PATH:str, authorCombinations, searchError:bool):
    # 排除在error.txt的combinations
    existCombinations = []
    if os.path.exists(ERROR_TXT_PATH):
        if searchError:# 若要搜尋error作者的話，就把error.txt清空，重新寫入錯誤的作者
            os.remove(ERROR_TXT_PATH)
        else:
            with open(ERROR_TXT_PATH, mode='r', encoding="UTF-8") as f:
                lines = f.readlines()
                lines = [x[:-1] for x in lines] # 去除換行符號
                for line in lines:
                    existCombinations.append(line.split('!@!')) 

    # 排除在domain.csv中查詢過的作者
    originalCoAuthorDF = readCSV(FILE_PATH) # 查詢過的作者的df
    if originalCoAuthorDF is not None:
        authorIDs1 = [str(x) for x in originalCoAuthorDF['AuthorID1'].to_list()]
        authorIDs2 = [str(x) for x in originalCoAuthorDF['AuthorID2'].to_list()]
        existCombinations.extend(zip(authorIDs1, authorIDs2))

    dropIdx = []
    print("remove exist combinations start!")
    print(len(authorCombinations))
    for existCombination in tqdm(existCombinations):
        for i in range(len(authorCombinations)):
            if authorCombinations[i][0].authorID == existCombination[0] and authorCombinations[i][1].authorID == existCombination[1]:
                dropIdx.append(i)
                break
        if len(dropIdx) == len(existCombinations): # 全部都drop完
            break

    authorCombinations = [authorCombinations[i] for i in range(len(authorCombinations)) if i not in dropIdx]


    # for existCombination in tqdm(existCombinations):
    #     authorCombinations = [x for x in authorCombinations if x[0].authorID==existCombination[0] and x[1].authorID==existCombination[1]]

    print("remove exist combinations complete!")
    print(len(authorCombinations))


    return authorCombinations


def collectSubFoldersData(ROOT_FILE_PATH:str):
    """
    Args : 
        ROOT_FILE_PATH : 
            合併檔案的跟目錄
            ex : ROOT設定為coAuthor/dirstibution0時，將收集dirstibution0底下所有subProcess的資料
            ex : ROOT設定為coAuthor/時，將收集coAuthor底下所有dirstibution的資料
    """

    # 合併coAuthor.csv
    csvFilePaths = glob.glob(f"{ROOT_FILE_PATH}/*/coAuthor.csv")

    dfs = []
    for csvFilePath in csvFilePaths:
        dfs.append(readCSV(csvFilePath))

    dfs = [x for x in dfs if x is not None] # drop None

    if len(dfs)>0:
        df = pd.concat(dfs, axis=0, ignore_index=True)
        originalCoAuthorDF = readCSV(f"{ROOT_FILE_PATH}/coAuthor.csv")
        if originalCoAuthorDF is not None: # 若舊的存在，則合併舊檔案
            newDF = pd.concat([originalCoAuthorDF, df], axis=0, ignore_index=True)
            newDF.to_csv(f"{ROOT_FILE_PATH}/coAuthor.csv", index=False, encoding='UTF-8')
        else:
            df.to_csv(f"{ROOT_FILE_PATH}/coAuthor.csv", index=False, encoding="UTF-8")


    # 合併error.txt
    errorFilePaths = glob.glob(f"{ROOT_FILE_PATH}/*/error.txt")
    if len(errorFilePaths)>0:
        errorLogs = []
        for errorFilePath in errorFilePaths:
            with open(errorFilePath, mode='r', encoding="UTF-8") as f:
                lines = f.readlines()
                errorLogs.extend(lines)

        with open(f"{ROOT_FILE_PATH}/error.txt", mode='a', encoding='UTF-8') as f:
            f.writelines(errorLogs)
