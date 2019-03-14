import argparse
import urllib.request
import handlers.SearchHandler as search
import handlers.AlbumHandler as album


def parse_search_url(url):
    base, query = url.split("?")
    params = urlparams_to_dict(query)
    rank, time = base.split("/")[-2:]
    return (rank, time, params)

def urlparams_to_dict(url):
    elems = [elem.split("=") for elem in url.split("&")]
    return {urllib.request.unquote(elem[0]): urllib.request.unquote(elem[1]) for elem in elems}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="command line tool to download imgur files")
    parser.add_argument("--urls", "-u",
                        help="urls to process (expects imgur gallery urls). Ignores search args if specified.",
                        nargs="+")
    parser.add_argument("--files", "-f",
                        help="urls to process that are stored in a text file (expects imgur gallery urls). Ignores search args if specified.",
                        nargs="+")
    parser.add_argument("--query", "-q", help="query to search for in imgur (will execute a basic search with no advanced params)")
    parser.add_argument("--rank", "-r", help="What to rank search results by, valid ranks are time, score, relevance (default time)")
    parser.add_argument("--time",
                        help="What timeframe to retrieve results from, valid timeframes are day, week, month, year, all (default all)")
    parser.add_argument("--limit", '-l', type=int, help="Number of search results to include, omit to take as many as possible")
    parser.add_argument("--mkdir", action="store_true",
                        help="Create a separate directory for each imgur album", default=False)
    parser.add_argument("--searchurl", "-s", help = "Performs a search using a Imgur Search url, rank and time are automatically parsed as well as any advanced search params")
    parser.add_argument("--appendparam", "-a", action="append", help= "Advanced: appends a key value pair to search request, should be of form key:value")
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
        with album.AlbumHandler() as ah:
            ah.download(urls, args.path, args.mkdir)
    if (args.rank not in allowed_types):
        args.rank = "time"

    if (args.time not in allowed_types):
        args.time = "all"

    query = search.SearchQuery(type=args.rank, time=args.time)
    if (args.query is not None):
        query.set_simple_query(args.query)
        with search.SearchHandler(query, limit) as sh:
            sh.download(args.path, args.mkdir)
        exit(0)

    if (args.searchurl is not None):
        rank, time, params = parse_search_url(args.searchurl)
        query = search.SearchQuery(rank, time)
        query.set_params(params)
        with search.SearchHandler(query, limit=limit) as sh:
            sh.download(args.path, args.mkdir)
        exit(0)

    if (args.appendparam is not None):
        params = {x:y for elem in args.appendparam for x,y in elem.split(":")}
        query = search.SearchQuery(args.rank, args.time)
        query.set_params(params)
        with search.SearchHandler(query, limit=limit) as sh:
            sh.download(args.path, args.mkdir)
        exit(0)


