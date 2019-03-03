import post
import requests
import utils
import argparse

def search_download():
    query = utils.SearchQuery(terms="Persona", type=utils.SearchQuery.SearchType.SCORE, time=utils.SearchQuery.SearchTime.ALL)
    handler = utils.SearchHandler(query, limit=100)
    ids = handler.fetch_image_ids()
    metadatas = handler.fetch_metadatas(ids, multithread=True)
    posts = post.create_posts(metadatas)
    print(type(metadatas[0]))
    print(type(posts[0]))
    #print(posts[0])
    #utils.download("./test/", *posts, multithread=True)

search_download()
if __name__ == "__main_":
    parser = argparse.ArgumentParser(description="command line tool to download imgur files")
    parser.add_argument("--urls",
                        help="urls to process (expects imgur gallery urls). Ignores search args if specified.",
                        nargs="+", action="append")
    parser.add_argument("--query", help="query to search for in imgur")
    parser.add_argument("--any", help="Include results that contain any of these terms")
    parser.add_argument("--exact", help="Include results that contain exactly this query")
    parser.add_argument("--not", help="Exclude results that contain any of these terms")
    parser.add_argument("--tags", help="Include results with these tags")
    parser.add_argument("--type",
                        help="Only include items with this type. Valid types are: jpg, png, gif, anigif, album")
    parser.add_argument("--rank", help="What to rank search results by, valid ranks are time, score, relevance")
    parser.add_argument("--time",
                        help="What timeframe to retrieve results from, valid timeframes are day, week, month, year, all")
    parser.add_argument("path", help="filepath to save images to")
    args = parser.parse_args()

