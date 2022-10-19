import pandas as pd
from copy import deepcopy
from tqdm import tqdm
import numpy as np
import multiprocessing
import itertools
import sys

sys.path.append("..")
from scopusCrawler.author import Author

def mp2(combinations, lst):
    for combination in tqdm(combinations):
        score = 0
        author1 = combination[0]
        author2 = combination[1]
        authorID1 = author1.authorID
        authorID2 = author2.authorID

        for domain in author1.domain:
            if domain in author2.domain:
                score = int(author1.domain[domain])*int(author2.domain[domain])

        lst.append([authorID1, authorID2, score])


if __name__ == '__main__':
    df = pd.read_csv("domainFromDOI/domain.csv", encoding="UTF-8")
    temp = df['Domain'].drop_duplicates().to_list()
    domains = []

    infos = df[['AuthorID', 'Domain', 'Num']].values.tolist()
    s = {}
    for info in tqdm(infos):
        authorID, domains, num = info
        authorID = str(authorID)
        if domains != 'None':
            domains = [x.replace(" ", "") for x in domains.split(";")]
        else:
            domains = []
        if authorID not in s:
            s[authorID] = Author(authorID=authorID)

        for domain in domains:
            s[authorID].setDomain(domain, str(num))


    mpNum = 16
    combinationSets = np.array_split(list(itertools.combinations(s.values(), 2)), mpNum)
    manager = multiprocessing.Manager()
    retv = manager.list()

    for i in range(mpNum):
        retv.append(manager.list())
        p = multiprocessing.Process(target=mp2, args=(combinationSets[i], retv[i]))
        p.start()

    for i in range(mpNum):
        p.join()

    data = []
    for r in retv:
        data.extend(r)


    df = pd.DataFrame(data, columns=['AuthorID1', 'AuthorID2', 'Score'])
    df.to_csv("domainScore.csv", encoding="UTF-8", index=False)

