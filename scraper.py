from bs4 import BeautifulSoup
import urllib.request as ur
import requests
import re
import time
import json
import sqlite3
import sys

CSS_TAGS = (
    "div.title>a",  # value includes title
    "div.title>a",  # href inculdes url
    "span.runtime",
    "div#user_rating>strong",
    "span.genre",
)


class Movies:
    def __init__(self):

        # Web Scraping
        page = requests.get("https://www.imdb.com/movies-in-theaters/")
        soup = BeautifulSoup(page.content, "lxml")

        f = lambda i: soup.select(CSS_TAGS[i])
        g = lambda x: range(len(f(x)))

        titles = [f(0)[i].text for i in g(0)]
        urls = ["https://www.imdb.com" + f(1)[i].attrs["href"] for i in g(1)]
        runtimes = [f(2)[i].text for i in g(2)]
        ratings = [float(f(3)[i].text) for i in g(3)]
        genres = [tuple(f(4)[i].text.strip().split(", ")) for i in g(4)]  # as tuple

        # generator comprehension
        movies = [list(x) for x in zip(titles, urls, runtimes, ratings, genres)]
        
        # Save/Open as json
        with open('lab3_movies_arr.json', 'w') as fh:
            json.dump(movies, fh)

        # open json obj from file
        with open("lab3_movies_arr.json", "r") as fh:
            movies = json.load(fh)
        # print(*movies, sep="\n", end="\n" * 2)  # DEBUG

        #Calculate genres
        srch = lambda x: len(re.findall(re.compile("'[A-Z][a-zA-Z\ ]+'"), str(x)))

        genres = [elem[-1] for elem in movies]

        max_genres = max([len(elem[-1]) for elem in movies])

        unique_genres = set(elem for lst in genres for elem in lst)


        # SQL
        conn = sqlite3.connect("lab3_movies.db")
        cur = conn.cursor()  # set cursor

        cur.execute("DROP TABLE IF EXISTS MoviesDB")

        cur.execute(
            """ CREATE TABLE MoviesDB(
                    m_id INTEGER NOT NULL PRIMARY KEY,
                    m_name TEXT,
                    m_link TEXT,
                    m_length INTEGER,
                    m_rating REAL)"""
        )

        # add the genre columns
        for i in range(max_genres):

            cur.execute(
                """ALTER TABLE MoviesDB ADD COLUMN {} INTEGER""".format(
                    "genre_" + str(i+1)
                )
            )

        conn.commit()  # commit changes to database

        for lst in movies:

            cur.execute(
                "INSERT INTO MoviesDB (m_name, m_link, m_length, m_rating) \
                VALUES (?, ?, ?, ?)",
                (lst[0], lst[1], lst[2].strip(" min"), lst[3]),
            )

        conn.commit()

        cur.execute("SELECT * FROM MoviesDB")

        col_names = [
            description[0] for description in cur.description
        ]

        results = cur.fetchall()

        cur.execute("DROP TABLE IF EXISTS GenresDB")

        cur.execute(
            """ CREATE TABLE GenresDB(
                    g_id INTEGER NOT NULL PRIMARY KEY,
                    g_genre TEXT UNIQUE ON CONFLICT IGNORE) """
        )

        # insert genre columns into GenresDB
        for elem in sorted(unique_genres):
            cur.execute(
                "INSERT INTO GenresDB (g_genre) VALUES (?)", (elem,)
            )

        conn.commit()

        cur.execute("SELECT * FROM GenresDB") # show all table contents

        results = cur.fetchall()  # results is a list of tuples

        for j in range(max_genres):
            # get the genre id based on genre name
            cur.execute(
                "SELECT g_id FROM GenresDB WHERE g_genre == ?",
                (j,),
            )

            genre_id = cur.fetchone()
            cur.execute(
                "UPDATE  MoviesDB SET genre_" + str(j+1) + " = ? WHERE m_id = ?",
                (genre_id, j+1),
            )

        cur.execute("SELECT m_id, m_name, genre_1, genre_2, genre_3 FROM MoviesDB")

        results = cur.fetchall()
        # print(*results)  # print table if needed

        # show all table contents
        cur.execute("SELECT * FROM MoviesDB")

        conn.commit()
        conn.close()  # close the connection when done with database

app = Movies()

