import pandas as pd
from collections import OrderedDict
from copy import deepcopy
from tqdm import tqdm
import numpy as np
import multiprocessing
import itertools

def mp1(infos, defaultDomains, lst):
    authors = {}
    for info in tqdm(infos):
        authorID, domains, num = info
        authors[str(authorID)] = deepcopy(defaultDomains)
        domains = [x.replace(" ", "") for x in domains.split(";")]
        for domain in domains:
            authors[str(authorID)][domain]+=int(num)

    lst.append(authors)

def mp2(combinations, authors, domains, lst):
    for combination in tqdm(combinations):
        score = 0
        authorID1 = combination[0]
        authorID2 = combination[1]
        for domain in domains:
            score+=authors[authorID1][domain] * authors[authorID2][domain]

        lst.append([authorID1, authorID2, score])


if __name__ == '__main__':
    df = pd.read_csv("domainFromDOI/domain.csv", encoding="UTF-8")
    temp = df['Domain'].drop_duplicates().to_list()
    domains = []
    defaultDomains = OrderedDict()

    for t in temp:
        domains.extend([x.replace(" ", "") for x in t.split(";")])

    domains = set(domains)

    for domain in domains:
        defaultDomains[domain] = 0

    infos = df[['AuthorID', 'Domain', 'Num']].values.tolist()
    mpNum = 16
    infoSets = np.array_split(infos, mpNum)
    authors = {}

    manager = multiprocessing.Manager()
    retv = manager.list()

    for i in range(mpNum):
        retv.append(manager.list())
        p = multiprocessing.Process(target=mp1, args=(infoSets[i], defaultDomains, retv[i]))
        p.start()

    for i in range(mpNum):
        p.join()

    for r in retv:
        authors.update(r[0])

    combinationSets = np.array_split(list(itertools.combinations(authors.keys(), 2)), mpNum)
    manager = multiprocessing.Manager()
    retv = manager.list()

    for i in range(mpNum):
        retv.append(manager.list())
        p = multiprocessing.Process(target=mp2, args=(combinationSets[i], authors, domains, retv[i]))
        p.start()

    for i in range(mpNum):
        p.join()

    data = []
    for r in retv:
        data.extend(r)


    df = pd.DataFrame(data, columns=['AuthorID1', 'AuthorID2', 'Score'])
    df.to_csv("domainScore.csv", encoding="UTF-8", index=False)
