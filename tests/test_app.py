from unittest import TestCase
import csv
import io
import os


from flask import Flask

from flask_pie import PieController
from flask_pie.utils import Formatter, DataIterator, MemoryzingTokenizer
from flask_pie.testing import FakeTagger
from flask_pie.formatters.glue import GlueFormatter


class TestGenericParameters(TestCase):
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
        tagger = FakeTagger(
            tokens=[
                [('Lasciva', ('lascivus', )), ('Roma', ('Roma', ))]
            ],
            tasks=["lemma"]
        )

        client = self.create(model_file=tagger)

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
        client.get("/api/?data=Lasciva Roma&lower=True")

        self.assertEqual(
            tagger.seen, [['lasciva', 'roma']]
        )

    def test_force_lower(self):
        """ Test the basic route with simple data but forcing lowering """
        tagger = FakeTagger(
            tokens=[
                [('Lasciva', ('lascivus', )), ('Roma', ('Roma', ))]
            ],
            tasks=["lemma"]
        )

        client = self.create(
            model_file=tagger,
            force_lower=True
        )
        response = client.get("/api/?data=Lasciva Roma")
        self.assertEqual(
            [["token", "lemma"], ["Lasciva", "lascivus"], ["Roma", "Roma"]],
            self.read_tsv(response),
            "TSV should be well generated"
        )
        self.assertEqual(
            tagger.seen, [['lasciva', 'roma']]
        )
        tagger.seen = []
        # Ask for lowering
        response = client.get("/api/?data=Lasciva Roma&lower=True")

        self.assertEqual(
            tagger.seen, [['lasciva', 'roma']]
        )

    def test_sent_tokenization(self):
        """ Test the basic route with simple data"""
        tagger = FakeTagger(
            tokens=[
                [('Lasciva', ('lascivus', )), ('Roma', ('Roma', ))],
                [('Virgo', ('virgo',)), ('est', ('sum',))]
            ],
            tasks=["lemma"]
        )

        client = self.create(
            model_file=tagger
        )

        response = client.get("/api/?data=Lasciva Roma. Virgo est.")
        self.assertEqual(
            [["token", "lemma"], ["Lasciva", "lascivus"], ["Roma", "Roma"], ["Virgo", "virgo"], ["est", "sum"]],
            self.read_tsv(response),
            "TSV should be well generated"
        )
        self.assertEqual(
            [['Lasciva', 'Roma', '.'], ['Virgo', 'est', '.']], tagger.seen,
            "Despite faking output, each sentence should be seen completelly"
        )

    def test_punct_reinsertion(self):
        """ Test the basic route with simple data"""
        tagger = FakeTagger(
            tokens=[
                [('Lasciva', ('lascivus', )), ('Roma', ('Roma', ))],
                [('Virgo', ('virgo',)), ('est', ('sum',))]
            ],
            tasks=["lemma"]
        )

        client = self.create(
            model_file=tagger,
            iterator=DataIterator(remove_from_input=DataIterator.remove_punctuation)
        )

        response = client.get("/api/?data=Lasciva Roma. Virgo est.")
        self.assertEqual(
            [
                ["token", "lemma"],
                ["Lasciva", "lascivus"],
                ["Roma", "Roma"],
                [".", ""],
                ["Virgo", "virgo"],
                ["est", "sum"],
                [".", ""]
            ],
            self.read_tsv(response),
            "The tagger should not receive any punctuation but it should be reinserted at response time"
        )
        self.assertEqual(
            [['Lasciva', 'Roma'], ['Virgo', 'est']],
            tagger.seen,
            "The tagger should not receive any punctuation but it should be reinserted at response time"
        )

    def test_glue_formatter(self):
        """ Check that glue formatter works okay ! """
        tokenizer = MemoryzingTokenizer(replacer=lambda x: x.replace("v", "u"))

        tagger = FakeTagger(**self.tagger_response_from_file("./data/fake1.tsv"))

        client = self.create(
            model_file=tagger,
            headers={"X-Accel-Buffering": "no"},
            formatter_class=GlueFormatter(tokenizer),
            force_lower=True,
            iterator=DataIterator(tokenizer=tokenizer, remove_from_input=DataIterator.remove_punctuation)
        )

        response = client.post("/api/", data={"data": "Latina qua bella sunt , , . Svnt bella , sumus."})

        self.assertEqual(
            """form	lemma	POS	morph	treated_token
latina	latina	NOMcom	Case=Nom|Numb=Plur	latina
qua	qua	ADVint	MORPH=empty	qua
bella	bellum	NOMcom	Case=Nom|Numb=Plur	bella
sunt	sum	VER	Numb=Plur|Mood=Ind|Tense=Pres|Voice=Act|Person=3	sunt
,	,	PUNC	MORPH=empty	,
,	,	PUNC	MORPH=empty	,
.	.	PUNC	MORPH=empty	.
svnt	sum	VER	Numb=Plur|Mood=Ind|Tense=Pres|Voice=Act|Person=3	sunt
bella	bellum	NOMcom	Case=Nom|Numb=Plur	bella
,	,	PUNC	MORPH=empty	,
sumus	sum	VER	Numb=Plur|Mood=Ind|Tense=Pres|Voice=Act|Person=1	sumus
.	.	PUNC	MORPH=empty	.""",
            response.data.decode().strip().replace("\r", ""),
            "morph should be glued, original token put back in, values should be changed"
        )

        self.assertEqual(
            [["latina", "qua", "bella", "sunt"], ["sunt", "bella", "sumus"]],
            tagger.seen,
            "Punctuation should not be seen, v should be Uified (Second sunt)"
        )
