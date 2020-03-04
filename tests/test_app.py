from unittest import TestCase
import csv
import io
import os


from flask import Flask
from flask_pie import PieController
from pie_extended.testing_utils import FakeAutoTag
from pie_extended.models.fro import Models
from pie_extended.models.fro.get import get_iterator_and_processor
from pie_extended.pipeline.formatters.proto import Formatter


class TestGenericParameters(TestCase):
    def create(self, **kwargs):
        defaults = dict(
            tagger=FakeAutoTag.from_model_string(Models, device="cpu"),
            get_iterator_and_processor=get_iterator_and_processor,
            formatter_class=Formatter
        )
        defaults["tagger"].lower = True
        defaults["tagger"].disambiguation = None
        defaults.update(kwargs)
        app = Flask(__name__)

        controller = PieController(**defaults)
        controller.init_app(app)

        client = app.test_client()

        return client, defaults["tagger"]

    def read_tsv(self, response):
        reader = csv.reader(io.StringIO(response.data.decode()), delimiter="\t")
        return list(iter(reader))

    def tagger_response_from_file(self, filepath):
        tasks = []
        tokens = [[]]
        with open(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            filepath
        )) as f:
            for index, row in enumerate(csv.reader(f, delimiter="\t")):
                if index == 0:
                    tasks = row[1:]
                elif len(row) == 0:
                    tokens.append([])
                else:
                    tokens[-1].append((row[0], tuple(row[1:])))
        return {"tasks": tasks, "tokens": tokens}

    def test_simple(self):
        """ Test the basic route with simple data"""
        client, tagger = self.create()

        response = client.get("/api/?data=Lasciva q'il Roma")
        self.assertEqual(
            [['token', 'lemma', 'POS', 'morph', 'treated'],
             ['Lasciva',
              'lemma0',
              'pos0',
              'MODE=MODE0|TEMPS=TEMPS0|PERS.=PERS0|NOMB.=NOMB0|GENRE=GENRE0|CAS=CAS0|DEGRE=DEGRE0',
              'Lasciva'],
             ["q'",
              'lemma1',
              'pos1',
              'MODE=MODE1|TEMPS=TEMPS1|PERS.=PERS1|NOMB.=NOMB1|GENRE=GENRE1|CAS=CAS1|DEGRE=DEGRE1',
              'q'],
             ['il',
              'lemma2',
              'pos2',
              'MODE=MODE2|TEMPS=TEMPS2|PERS.=PERS2|NOMB.=NOMB2|GENRE=GENRE2|CAS=CAS2|DEGRE=DEGRE2',
              'il'],
             ['Roma',
              'lemma3',
              'pos3',
              'MODE=MODE3|TEMPS=TEMPS3|PERS.=PERS3|NOMB.=NOMB3|GENRE=GENRE3|CAS=CAS3|DEGRE=DEGRE3',
              'Roma']],
            self.read_tsv(response),
            "TSV should be well generated"
        )
