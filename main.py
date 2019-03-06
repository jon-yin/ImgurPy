import requests

import post
import utils
import argparse

def search_download():
    query = utils.SearchQuery(terms="java", type=utils.SearchQuery.SearchType.SCORE, time=utils.SearchQuery.SearchTime.ALL)
    handler = utils.SearchHandler(query, limit=50)
    ids = handler.fetch_image_ids()
    metadatas = handler.fetch_metadatas(ids, multithread=True)
    posts = post.create_posts(metadatas)
    utils.download("./test/", *posts, multithread=True, create_album_directory=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="command line tool to download imgur files")
    parser.add_argument("--urls", "-u",
                        help="urls to process (expects imgur gallery urls). Ignores search args if specified.",
                        nargs="+", action="append")
    parser.add_argument("--query", "-q", help="query to search for in imgur")
    parser.add_argument("--any", "-a", help="Include results that contain any of these terms")
    parser.add_argument("--exact", "-e", help="Include results that contain exactly this query")
    parser.add_argument("--not", "-n", help="Exclude results that contain any of these terms")
    parser.add_argument("--tags", help="Include results with these tags")
    parser.add_argument("--type",
                        help="Only include items with this type. Valid types are: jpg, png, gif, anigif, album")
    parser.add_argument("--rank" "-r", help="What to rank search results by, valid ranks are time, score, relevance")
    parser.add_argument("--time",
                        help="What timeframe to retrieve results from, valid timeframes are day, week, month, year, all")
    parser.add_argument("path", help="filepath to save images to")
    args = parser.parse_args()
    print(args.urls)

