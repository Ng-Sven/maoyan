import requests
from lxml import etree
import pymongo
from maoyantop100 import setting
from requests.exceptions import ConnectionError



class MaoYan(object):
    def __init__(self):
        self.url = "https://maoyan.com/board/4?offset={}"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
        }
        self.client = pymongo.MongoClient(host=setting.MONGO_HOST,port=setting.MONGO_PORT)
        self.mongodb = self.client[setting.MONGODB_NAME]
        self.collection = self.mongodb["movie"]

    def parse(self,url):
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                print("获取失败")
                self.parse(url)
            return response.content.decode()
        except ConnectionError as e:
            print("ConnectionError:",e)

    def get_data(self,html_str):
        html = etree.HTML(html_str)
        dd_list = html.xpath("//dl[@class='board-wrapper']/dd")
        item_list = []
        for dd in dd_list:
            item = {}
            item["sort"] = dd.xpath("./i/text()")[0]
            item["star"] = dd.xpath(".//p[@class='star']/text()")[0].strip().split("：")[1]
            item["detail_url"] = dd.xpath("./a[@class='image-link']/@href")[0]
            item["detail_url"] = "https://maoyan.com" + item["detail_url"]
            detail_html = self.parse(item["detail_url"])
            item = self.get_detail_data(detail_html,item)
            print(item)
            item_list.append(item)
            # time.sleep(3)
        return item_list

    def get_detail_data(self, html_str, item):
        item = item
        html = etree.HTML(html_str)
        item["name"] = html.xpath("//h3[@class='name']/text()")[0]
        item["ename"] = html.xpath("//div[@class='ename ellipsis']/text()")[0]
        item["img_url"] = html.xpath("//div[@class='avatar-shadow']/img/@src")[0]
        item["category"] = html.xpath("//div[@class='movie-brief-container']/ul/li[1]/text()")
        item["position"] = html.xpath("//div[@class='movie-brief-container']/ul/li[2]/text()")[0].split()[0]
        item["minute"] = html.xpath("//div[@class='movie-brief-container']/ul/li[2]/text()")[0].split()[2]
        item["score"] = html.xpath("//span[@class='stonefont']/text()")[0]
        item["money"] = "".join(html.xpath("//div[@class='movie-index']/div/span/text()")).strip()
        item["drama"] = html.xpath("//span[@class='dra']/text()")[0].strip()
        item["director"] = html.xpath("//*[@id='app']/div/div[1]/div/div[2]/div[2]/div/div[1]/ul/li/div/a/text()")[0].strip()
        return item


    def save_data(self,item):
        self.collection.insert(item)

    def run(self):
        # 获取url，以及后面的url
        # url的规律是后面的为0，10，20等
        for i in range(10):
            i = i * 10
            url = self.url.format(i)
        # 提取url的html
            html_str = self.parse(url)
            if html_str is None:
                pass
            # 提取html中要爬取的内容
            item_list = self.get_data(html_str)
            # 存储提取的信息
            for item in item_list:
                self.save_data(item)


def main():
    maoyan = MaoYan()
    maoyan.run()

if __name__ == '__main__':
    main()