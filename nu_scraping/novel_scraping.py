import scraper as nu_scraper

novel_scraper = nu_scraper.NovelScraper(debug=True)
novel_id = novel_scraper.get_all_novel_ids()
print(novel_id)
novel_dict = novel_scraper.parse_single_novel(novel_id[0])
print(novel_dict)
