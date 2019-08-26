from unittest import TestCase
import csv
import io

from flask import Flask

from flask_pie import PieController
from flask_pie.utils import Formatter, DataIterator, Tokenizer
from flask_pie.testing import FakeTagger


class IntegrationTest(TestCase):
    def create(self, **kwargs):
        defaults = dict(
            formatter_class=Formatter,
            iterator=DataIterator(),
            device="cpu"
        )
        defaults.update(kwargs)
        app = Flask(__name__)

        controller = PieController(**defaults)
        controller.init_app(app)

        client = app.test_client()

        return client

    def read_tsv(self, response):
        reader = csv.reader(io.StringIO(response.data.decode()), delimiter="\t")
        return list(iter(reader))

    def test_simple(self):
        tagger = FakeTagger(
            tokens=[
                [('Lasciva', ('lascivus', )), ('Roma', ('Roma', ))]
            ],
            tasks=["lemma"]
        )

        client = self.create(
            model_file=tagger
        )
        response = client.get("/api/?data=Lasciva Roma")
        self.assertEqual(
            [["token", "lemma"], ["Lasciva", "lascivus"], ["Roma", "Roma"]],
            self.read_tsv(response),
            "TSV should be well generated"
        )
        self.assertEqual(
            tagger.seen, [['Lasciva', 'Roma']]
        )
        tagger.seen = []
        # Ask for lowering
        response = client.get("/api/?data=Lasciva Roma&lower=True")

        self.assertEqual(
            tagger.seen, [['lasciva', 'roma']]
        )
