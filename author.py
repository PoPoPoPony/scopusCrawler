

class Author:
    def __init__(self, originalName:str=None, lastName:str=None, firstName:str=None, authorID:str=None) -> None:
        self.originalName = originalName
        self.firstName = firstName
        self.lastName = lastName
        self.authorID = authorID
        self.article = {}
        self.domain = {}


    def setArticle(self, title:str, num:str):
        num = eval(num.replace(',', ''))

        # if title in self.article:
        #     print(f"[Warning! repeat]{title}, {num}")


        self.article[title] = self.article.setdefault(title, 0)+num
        # if title not in self.article:
        #     self.article[title] = num 

    def setDomain(self, domain:str, num:str):
        num = eval(num.replace(',', ''))
        self.domain[domain] = self.article.setdefault(domain, 0)+num
