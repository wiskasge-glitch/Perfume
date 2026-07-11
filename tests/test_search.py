from app.scraper.search import SearchBuilder


def main():

    url = (
        SearchBuilder()
        .keyword("versace eros")
        .build()
    )

    print(url)

    url = (
        SearchBuilder()
        .keyword("lattafa khamrah")
        .min_price(500)
        .max_price(1200)
        .build()
    )

    print(url)


if __name__ == "__main__":
    main()