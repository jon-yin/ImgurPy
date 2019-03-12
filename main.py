import requests

import post
import utils
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="command line tool to download imgur files")
    parser.add_argument("--urls", "-u",
                        help="urls to process (expects imgur gallery urls). Ignores search args if specified.",
                        nargs="+")
    parser.add_argument("--files", "-f",
                        help="urls to process that are stored in a text file (expects imgur gallery urls). Ignores search args if specified.",
                        nargs="+")
    parser.add_argument("--query", "-q", help="query to search for in imgur")
    parser.add_argument("--all",  help="Include results that contain all of these terms")
    parser.add_argument("--any",  help="Include results that contain any of these terms")
    parser.add_argument("--exact", "-e", help="Include results that contain exactly this query")
    parser.add_argument("--none", "-n", help="Exclude results that contain any of these terms")
    parser.add_argument("--tags", help="Include results with these tags")
    parser.add_argument("--type",
                        help="Only include items with this type. Valid types are: jpg, png, gif, anigif, album")
    parser.add_argument("--rank", "-r", help="What to rank search results by, valid ranks are time, score, relevance (default time)")
    parser.add_argument("--time",
                        help="What timeframe to retrieve results from, valid timeframes are day, week, month, year, all (default all)")
    parser.add_argument("--limit", '-l', type=int, help="Number of search results to include, omit to take as many as possible")
    parser.add_argument("--mkdir", action="store_true",
                        help="Create a separate directory for each imgur album", default=False)
    parser.add_argument("--size", "-s", help = "Size of desired images, valid inputs are small, med, big, lrg, huge")
    parser.add_argument("path", help="filepath to save images to")
    args = parser.parse_args()
    allowed_times = {"day", "week", "month", "year", "all"}
    allowed_types = {"time", "score", "relevance"}
    if args.limit:
        limit = args.limit
    else:
        limit = float("inf")
    if (args.urls is not None or args.files is not None):
        urls = []
        if (args.urls is not None):
            urls = args.urls
        if (args.files is not None):
            for file in args.files:
                with open(file, "r") as fh:
                    urls.extend(fh.readlines())
        with utils.AlbumHandler() as ah:
            ah.download(urls, args.path, args.mkdir)
    if (args.rank not in allowed_types):
        args.rank = "time"

    if (args.time not in allowed_types):
        args.time = "all"

    query = utils.SearchQuery(type=args.rank, time=args.time)
    if (args.query is not None):
        query.set_simple_query(args.query)
        with utils.SearchHandler(query, limit) as sh:
            sh.download(args.path, args.mkdir)
        exit(0)

    params = {}
    if (args.all):
        params["q_all"] = args.all
    if (args.any):
        params["q_any"] = args.any
    if (args.exact):
        params["q_exact"] = args.exact
    if (args.none):
        params["q_not"] = args.none
    if (args.tags):
        params["q_tags"] = args.tags
    if (args.type):
        params["q_type"] = args.type
    if (args.size):
        sizes = {"small", "med", "big", "lrg", "huge"}
        if (args.size in sizes):
            params["q_size_px"] = args.size
            params["q_size_mpx"] = args.size
    if (len(params) > 0):
        query.set_params(params)
        with utils.SearchHandler(query, limit) as sh:
            sh.download(args.path, args.mkdir)

