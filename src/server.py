from typing import Tuple, List

import sqlalchemy
from flask import Flask, render_template
from sqlalchemy.orm import sessionmaker

from src.constants import CONN_STRING
from src.database_model import Item
from src.scrapy_sreality.scrapy_sreality.spiders.web_crawler import run_scrapy

app = Flask(__name__, template_folder='/web_test/src/templates')


def get_ads(session) -> List[Tuple[str, str]]:
    # retrieve first 500 items from database
    items = session.query(Item).order_by(Item.id.desc()).limit(500).all()[::-1]
    return [(item.title, item.image) for item in items]


@app.route('/')
def render():
    engine = sqlalchemy.create_engine(CONN_STRING)
    session = sessionmaker(bind=engine)()
    content = get_ads(session)  # get content from database
    session.close()
    engine.dispose()
    return render_template('index.html', content=content)


if __name__ == '__main__':
    # first run scrapy crawling of sreality.cz flats/sell and store results to database
    run_scrapy()

    # run flask server
    app.run(host='0.0.0.0', port=8080)
