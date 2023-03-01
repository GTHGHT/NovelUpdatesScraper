import cloudscraper
from bs4 import BeautifulSoup


class ProcessSeriesFinder:

    def __init__(self):
        self.scraper = cloudscraper.create_scraper()

    def get_sf_info(self, url):
        page = self.scraper.get(url)
        if page.status_code == 200:
            soup = BeautifulSoup(page.text, "html.parser")
            return self._parse_sf_info(soup)

    def _parse_sf_info(self, soup):
        content = soup.find("div", {"class": "w-blog-content other"})
        novel_list = content.findAll("div", {"class": "search_main_box_nu"})
        sf_info = []
        for novel in novel_list:
            novel_info = dict()
            novel_info.update(self._get_item(novel))
            genre_sect = novel.find("div", attrs={"class": "search_genre"})
            novel_info.update(self._get_genre(genre_sect))
            sf_info.append(novel_info)

        return sf_info

    @staticmethod
    def _get_item(soup):
        item_info = dict()
        sid = soup.find("span", attrs={"class": "rl_icons_en"})
        item_info["id"] = sid.get("id")[3:]
        item_info["title"] = soup.find("a").text
        item_info["image"] = soup.find("img").get("src")

        return item_info

    @staticmethod
    def _get_genre(soup):
        genres_id = []
        genres = []
        for genre in soup.findAll("a"):
            genres_id.append(genre.get("gid"))
            genres.append(genre.text)
        return dict(genre_id=genres_id, genre=genres)


class ProcessNovel:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()

    def get_novel_info(self, url):
        page = self.scraper.get(url)
        if page.status_code == 200:
            soup = BeautifulSoup(page.text, features="html.parser")
            content = soup.find("div", attrs={"class": "w-blog-content"})
            novel_info = dict()
            novel_info.update(self._get_general_info(soup))
            novel_info.update(self._get_detail_info(content))
            novel_info.update(self._get_creators_info(content))
            return novel_info
        else:
            return dict()

    @staticmethod
    def _get_general_info(soup):
        general_info = dict()
        novel_link = soup.find("link", {"rel": "shortlink"}).get("href")
        general_info["sid"] = novel_link.split("p=")[-1]
        general_info["title"] = soup.find("div", {"class": "seriestitlenu"}).text
        general_info["novel_link"] = novel_link
        general_info["img_link"] = soup.find("img").get("src")
        general_info["description"] = soup.find("meta", attrs={"property": "description"}).get("content")

        return general_info

    @staticmethod
    def _get_detail_info(soup):
        detail_info = dict()
        sidebar = soup.find("div", {"class": "wpb_wrapper"})
        detail_info["language"] = sidebar.find("a", {"class": "genre lang"}).text
        detail_info["type"] = sidebar.find("div", {"id": "showtype"}).text.strip()
        detail_info["year"] = sidebar.find("div", {"id": "edityear"}).text.strip()
        detail_info["rating"] = sidebar.find("span", {"class", "uvotes"}).text[1:4]

        # add all genre id and genre name
        genre_list = sidebar.find("div", {"id": "seriesgenre"})
        genre_id = list()
        genre_name = list()

        for genre in genre_list.find_all("a"):
            genre_id.append(genre.get("gid"))
            genre_name.append(genre.text)

        detail_info["genre_id"] = genre_id
        detail_info["genre"] = genre_name

        # add all tags
        tag_list = sidebar.find("div", {"id": "showtags"})
        detail_info["tag"] = [tag.text for tag in tag_list.find_all("a")]

        return detail_info

    @staticmethod
    def _get_creators_info(soup):
        creators_info = dict()

        author_list = soup.find("div", {"id": "showauthors"})
        authors = author_list.find_all("a")
        if authors:
            creators_info["authors"] = [author.text for author in authors]

        artist_list = soup.find("div", {"id": "showartists"})
        artists = artist_list.find_all("a")
        if artists:
            creators_info["artists"] = [artist.text for artist in artists]

        return creators_info

    @staticmethod
    def _get_reccomended_info(soup):
        main_content = soup.find("div", {"class": "wpb_wrapper"})
        recc_list = main_content.findAll("a", {"class": "genre"}, limit=6)
        recommended_info = list()
        for recc in recc_list:
            recommended_info.append(dict(id=recc.get("id")[3:], title=recc.text))
        return dict(recommendations=recommended_info)


class ProcessFilter:

    def __init__(self):
        self.SERIES_FINDER = "https://www.novelupdates.com/series-finder/"
        self.filters = list()
        self.scraper = cloudscraper.create_scraper()
        self.updateFilter()

    def updateFilter(self):
        page = self.scraper.get(self.SERIES_FINDER)
        if page.status_code == 200:
            soup = BeautifulSoup(page.content, "html.parser")
            self._parseFilter(soup)

    def _parseFilter(self, soup):
        filter_list = dict()
        filter_sect = soup.find_all("div", {"class": "g-cols wpb_row offset_default"}, limit=5)
        
        ntype_list = filter_sect[0].find_all("a", {"class": "typerank"})
        filter_list["novel_type"] = [{"id": i.get("genreid"), "name": i.text} for i in ntype_list]
        
        language_list = filter_sect[1].find_all("a", {"class": "langrank"})
        filter_list["language"] = [{"id": i.get("genreid"), "name": i.text} for i in language_list]

        # Genre
        genre_list = filter_sect[2].find_all("a", {"class": "genreme"})
        filter_list["genre"] = [{"id": i.get("genreid"), "name": i.text} for i in genre_list]

        # Tag
        tag_list = filter_sect[3].find("select", {"class": "chzn-select"}).find_all("option")
        filter_list["tag"] = [{"id": i.get("value"), "name": i.text} for i in tag_list]

        # Story Status
        sstatus_sect = soup.find("select", {"name": "storystatus"})
        sstatus_type = sstatus_sect.find_all("option")
        filter_list["story_status"] = [{"id": i.get("value"), "name": i.text} for i in sstatus_type]

        # Sort
        sort_sect = filter_sect[4].find("select", {"name": "sortmyresults"})
        sort_list = sort_sect.find_all("option")
        filter_list["sort"] = [{"id": i.get("value"), "name": i.text} for i in sort_list]

        # Order
        order_sect = filter_sect[4].find("select", {"name": "sortmyorder"})
        order_list = order_sect.find_all("option", limit=2)
        filter_list["order"] = [{"id": i.get("value"), "name": i.text} for i in order_list]

        self.filters = filter_list

    def getFilter(self):
        return self.filters


class NUScraper:
    # Buat API Disini

    pass


if __name__ == '__main__':
    novel = ProcessFilter()
    print(novel.getFilter())