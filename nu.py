import json
from typing import Union

import cloudscraper
from bs4 import BeautifulSoup


class NUScraper:

    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.json_encoder = json.JSONEncoder()
        self.SERIES_FINDER = "https://www.novelupdates.com/series-finder/"
        self.NOVEL = "http://www.novelupdates.com/?p="

    def parse_series_finder(self, page, ntype=None, language=None, nchapters=None, release_frequency=None, reviews=None,
                            rating=None, nratings=None, readers=None, first_date=None, last_date=None,
                            genre_included: list[Union[list[str], str]] = None, genre_excluded=None,
                            tags_included: list[Union[list[str], str]] = None, tags_excluded=None, status=None,
                            sort="sdate", order="desc"):
        """
        Parses a single novel updates series finder page

        This Function Return JSON of the series info in the all of series finder page. The Series info consists
        of series's id, title, genre id list, genre list and image link.

        Args:
            page(int): page number
            ntype(str): novel type filter
            language(str): novel language filter
            nchapters(list[str, str]): numbers of chapters filter with qualifier 'min' or 'max'
            release_frequency(list[str, str]): release frequency filter with qualifier 'min' or 'max'
            reviews(list[str, str]): numbers of reviews filter with qualifier 'min' or 'max'
            rating(list[str, str]): rating filter with qualifier 'min' or 'max'
            nratings(list[str, str]): numbers of ratings filter with qualifier 'min' or 'max'
            readers(list[str, str]): numbers of readers filter with qualifier 'min' or 'max'
            first_date(list[str, str]): first date filter with qualifier 'min' or 'max'
            last_date(list[str, str]): last date filter with qualifier 'min' or 'max'
            genre_included: genre included filter with qualifier 'and' or 'or'
            genre_excluded(Union[list[str]]): genre excluded filter
            tags_included: tags included filter with qualifier 'and' or 'or'
            tags_excluded(Union[list[str]]):tags excluded filter
            status(str): novel status filter
            sort(str): sort based on filter
            order(str): the order of the novel (asc or desc)

        Returns:
            str: JSON converted from the list of various novel's info in the page
        """
        url = self.SERIES_FINDER + str(page) + "/?sf=1"
        if ntype:
            url += "&nt=" + ntype
        if language:
            url += "&org=" + language
        if nchapters:
            url += "&rl=" + nchapters[0] + "&mrl=" + nchapters[1]
        if release_frequency:
            url += "&rf=" + release_frequency[0] + "&mrf=" + release_frequency[1]
        if reviews:
            url += "&rvc=" + reviews[0] + "&mrvc=" + reviews[1]
        if rating:
            url += "&rt=" + rating[0] + "&mrt=" + reviews[1]
        if nratings:
            url += "&rtc=" + nratings[0] + "&mrtc=" + nratings[1]
        if readers:
            url += "&rct=" + readers[0] + "&mrct=" + readers[1]
        if first_date:
            url += "&dtf=" + first_date[0] + "&mdtf=" + first_date[1]
        if last_date:
            url += "&dt=" + last_date[0] + "&mdt=" + last_date[1]
        if genre_included:
            gi = "&gi="
            for count, i in enumerate(genre_included[0]):
                gi += i if count == 0 else "," + i
            url += gi + "&mgi=" + genre_included[1]
        if genre_excluded:
            ge = "&ge="
            for count, i in enumerate(genre_excluded[0]):
                ge += i if count == 0 else "," + i
            url += ge
        if tags_included:
            tgi = "&tgi="
            for count, i in enumerate(tags_included[0]):
                tgi += i if count == 0 else "," + i
            url += tgi + "&mtgi=" + tags_included[1]
        if tags_excluded:
            tge = "&tge="
            for count, i in enumerate(tags_excluded[0]):
                tge += i if count == 0 else "," + i
            url += tge
        if status:
            url += "&ss=" + status
        url += "&sort=" + sort + "&order=" + order
        page = self.scraper.get(url)
        if page.status_code == 200:
            soup = BeautifulSoup(page.text, "html.parser")
            sf_json = self.json_encoder.encode(self.get_sf_info(soup))
            return sf_json
        else:
            return self.json_encoder.encode(dict())

    @staticmethod
    def get_sf_info(content):
        content_div = content.find("div", {"class": "w-blog-content other"})
        novel_div = content_div.findAll("div", {"class": "search_main_box_nu"})
        novel_list = []
        for i in range(len(novel_div)):
            sid_div = novel_div[i].find("span", attrs={"class": "rl_icons_en"})
            sid = sid_div.get("id").strip("sid")
            title_div = novel_div[i].find("a")
            genre_div = novel_div[i].findAll("a", attrs={"class": "gennew search"})
            image_div = novel_div[i].find("img", attrs={"dp": "yes"})
            novel_list += [{
                "id": sid,
                "title": title_div.text,
                "genre_id": [i.get("gid") for i in genre_div],
                "genre": [i.text for i in genre_div],
                "image_link": image_div.get("src")
            }]

        return novel_list

    def parse_novel(self, novel_id, full_url=False):
        if full_url is False:
            url = self.NOVEL + str(novel_id)
        else:
            url = str(novel_id)
        page = self.scraper.get(url)
        if page.status_code == 200:
            soup = BeautifulSoup(page.text, features="html.parser")
            full_content = soup.find("div", attrs={"class": "l-main"})
            content = soup.find("div", attrs={"class": "w-blog-content"})
            novel_info = {"sid": novel_id}
            novel_info.update(self.get_general_info(content))
            novel_info.update(self.get_desc(full_content))
            novel_info.update(self.get_detail_info(content))
            novel_info.update(self.get_creators_info(content))
            novel_json = self.json_encoder.encode(novel_info)
            return novel_json
        else:
            return self.json_encoder.encode(dict())

    @staticmethod
    def get_general_info(content):
        general_info = dict()
        general_info["title"] = content.find("div", {"class": "seriestitlenu"}).text
        general_info["img_link"] = content.find("img").get("src")
        general_info["language"] = content.find("a", {"class": "genre lang"}).text
        return general_info

    @staticmethod
    def get_detail_info(content):
        detail_info = dict()
        sidebar = content.find("div", {"class": "wpb_wrapper"})
        detail_info["type"] = sidebar.find("div", {"id": "showtype"}).text
        detail_info["year"] = sidebar.find("div", {"id": "edityear"}).text
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
    def get_creators_info(content):
        creators_info = dict()

        author_list = content.find("div", {"id": "showauthors"})
        authors = author_list.find_all("a")
        if authors:
            creators_info["authors"] = [author.text for author in authors]

        artist_list = content.find("div", {"id": "showartists"})
        artists = artist_list.find_all("a")
        if artists:
            creators_info["artists"] = [artist.text for artist in artists]

        return creators_info

    @staticmethod
    def get_reccomended_info(content):
        main_content = content.find("div", {"class": "wpb_wrapper"})
        recc_list = main_content.findAll("a", {"class": "genre"}, limit=6)
        recommended_info = list()
        for recc in recc_list:
            recommended_info.append(dict(id=recc.get("id")[3:], title=recc.text))
        return dict(recommendations=recommended_info)

    @staticmethod
    def get_desc(content):
        desc_text = content.find("meta", property="og:description", content=True)
        desc = desc_text.get("content")
        return dict(description=desc)

    # @staticmethod
    # def get_reviews(content):
    #     reviews_list = content.find("div", attrs={"class": "w-comments-list"})
    #     reviews = reviews_list.findAll("div", attrs={"class": "w-comments-item"})
    #     for count,review in enumerate(reviews):
    #         rev_name = review.find("a", attrs={"id": "revname"})
    #         rev_stars = review.findAll("i",attrs={"id": "fa fa-star"}, limit=5)
    #         rev_date = review.find("div", attrs={"style": "text-align: right;"})
    #
    #     pass

    # @staticmethod
    # def get_novel_info(content):
    #     content_div = content.find("div", {"class": "l-content"})
    #     title = content_div.find("div", atrrs={"class": "seriestitlenu"})
    #     img = content_div.find("img")
    #     type = content_div.find("a", attrs={"class": "genre type"})
    #     genre_div = content_div.find("div", attrs={"class": "seriesgenre"})
    #     genre_list = genre_div.findAll("a", attrs={"class": "genre"})
    #     tags_div = content_div.find("div", attrs={"class": "seriesgenre"})
    #     tags_list = tags_div.findAll("a", attrs={"id": "etagme"})
    #     rating_table = content_div.find("table", attrs={"id": "myrates"})
    #     rating_list = content_div.findAll("span", attrs={"class": "votetext"})
    #     language = content_div.find("a", attrs={"class": "genre lang"})
    #     authors_div = content_div.find("div", attrs={"id": "showauthors"})
    #     authors_list = authors_div.find_all("a", attrs={"id": "authtag"})
    #     artists_div = content_div.find("div", {"id": "showartists"})
    #     artists_list = artists_div.find_all("a", {"id": "artiststag"})
    #     year = content_div.find("div", attrs={"id": "edityear"})
    #     status = content_div.find("div", attrs={"id": "edityear"})

    def get_filters_list(self):
        """Get filters list

        The function scrapes NU Series Finder to get the filters list which
        consists of novel language, genre and tags. The novel type, status and
        sort filter is not included because they don't change.

        Returns:
            str: JSON from the list of filters on novel updates
        """
        page = self.scraper.get(self.SERIES_FINDER)
        if page.status_code == 200:
            page_soup = BeautifulSoup(page.text, "html.parser")
            filter_div = page_soup.find_all("div", {"class": "g-cols wpb_row offset_default"})
            language_list = filter_div[1].find_all("a", {"class": "langrank"})
            genre_list = filter_div[2].find_all("a", {"class": "genreme"})
            tags_list = filter_div[3].find("select", {"class": "chzn-select"}).find_all("option")
            filter_list = {
                "language": [{
                    "id": i.get("genreid"),
                    "name": i.text
                } for i in language_list],
                "genre": [{
                    "id": i.get("genreid"),
                    "name": i.text
                } for i in genre_list],
                "tags": [{
                    "id": i.get("genreid"),
                    "name": i.text
                } for i in tags_list]
            }
            return self.json_encoder.encode(filter_list)


if __name__ == "__main__":
    novel_list = [r"https://www.novelupdates.com/series/the-regressor-and-the-blind-saint/ "
                  r"https://www.novelupdates.com/series/every-night-i-come-to-his-bedroom/ ",
                  r"https://www.novelupdates.com/series/a-terminally-ill-villainess-refuses-to-be-adopted/ ",
                  r"https://www.novelupdates.com/series/the-flower-with-a-sword/ ",
                  r"https://www.novelupdates.com/series/i-was-a-man-before-reincarnating-so-i-refuse-a-reverse-harem/",
                  r"https://www.novelupdates.com/series/im-worried-that-my-brother-is-too-gentle/",
                  r"https://www.novelupdates.com/series/my-sister-picked-up-the-male-lead/",
                  r"https://www.novelupdates.com/series/the-ladys-butler/",
                  r"https://www.novelupdates.com/series/becoming-the-villains-family/",
                  r"https://www.novelupdates.com/series/ending-maker/",
                  r"https://www.novelupdates.com/series/im-really-not-the-demon-gods-lackey/",
                  r"https://www.novelupdates.com/series/since-ive-entered-the-world-of-romantic-comedy-manga-ill-do"
                  r"-my-best-to-make-the-heroine-who-doesnt-stick-with-the-hero-happy/ ",
                  r"https://www.novelupdates.com/series/i-was-reincarnated-in-a-yandere-main-love-comedy-game-and"
                  r"-suddenly-a-dangerous-girl-became-my-younger-sister/ "
                  ]

    nu_scraper = NUScraper()

    # print(nu_scraper.get_filters_list())
    # for novel in novel_list:
    #     print(nu_scraper.parse_novel(novel, full_url=True))
    #     print()
    #
    # nu_scraper.parse_series_finder(1)

    print(nu_scraper.parse_novel(r"https://www.novelupdates.com/series/the-regressor-and-the-blind-saint/ ", full_url=True))
