from flask import Blueprint, request, Flask, Response, stream_with_context
from typing import Iterator
from pie.tagger import Tagger
from pie.utils import chunks, model_spec

from .testing import FakeTagger
from .utils import DataIterator, Tokenizer, Formatter


class PieController(object):
    def __init__(self,
                 path: str = "/api", name: str = "nlp_pie", iterator: DataIterator=None, device: str = None,
                 batch_size: int = None, model_file: str = None, formatter_class: Formatter = None,
                 headers = None, force_lower=False):

        self._bp: Blueprint = Blueprint(name, import_name=name, url_prefix=path)
        self.tokenizer: Tokenizer = None
        self.force_lower = force_lower
        self.formatter_class = formatter_class or Formatter
        self.batch_size = batch_size
        self.model_file = model_file
        self.headers = {
            'Content-Type': 'text/plain; charset=utf-8',
            'Access-Control-Allow-Origin': "*"
        }
        if isinstance(headers, dict):
            self.headers.update(headers)

        if isinstance(model_file, FakeTagger):
            self.tagger = model_file
        else:
            self.tagger = Tagger(device=device, batch_size=batch_size)

            for model, tasks in model_spec(model_file):
                self.tagger.add_model(model, *tasks)

        self.iterator = iterator
        if not iterator:
            self.iterator = DataIterator()

    def init_app(self, app: Flask):
        self._bp.add_url_rule("/", view_func=self.route, endpoint="main", methods=["GET", "POST", "OPTIONS"])
        app.register_blueprint(self._bp)

    def route(self):
        return Response(
               stream_with_context(self.csv_stream()),
               200,
               headers=self.headers
        )

    def csv_stream(self) -> Iterator[str]:
        """ CSV Streaming function for the API response

        :return:
        """
        if self.force_lower:
            lower = True
        else:
            lower = request.args.get("lower", False)
            if lower:
                lower = True

        if request.method == "GET":
            data = request.args.get("data")
        else:
            data = request.form.get("data")

        if not data:
            yield ""
        else:
            yield from self.build_response(
                data,
                lower=lower,
                iterator=self.iterator,
                batch_size=self.batch_size,
                tagger=self.tagger,
                formatter_class=self.formatter_class
            )

    @staticmethod
    def build_response(data, iterator, lower, batch_size, tagger, formatter_class):
        header = False
        formatter = None
        for chunk in chunks(iterator(data, lower=lower), size=batch_size):
            # Unzip the batch into the sentences, their sizes and the dictionaries of things that needs
            #  to be reinserted
            sents, lengths, needs_reinsertion = zip(*chunk)

            tagged, tasks = tagger.tag(sents=sents, lengths=lengths)
            formatter = formatter_class(tasks)

            for sent, sent_reinsertion in zip(tagged, needs_reinsertion):
                if not header:
                    yield formatter.write_headers()
                    header = True

                yield formatter.write_sentence_beginning()

                reinsertion_index = 0
                index = 0
                for index, (token, tags) in enumerate(sent):

                    if reinsertion_index + index in sent_reinsertion:
                        yield formatter.write_line(
                            formatter.format_line(
                                token=sent_reinsertion[reinsertion_index + index],
                                tags=[""]*len(tasks)
                            )
                        )
                        del sent_reinsertion[reinsertion_index + index]
                        reinsertion_index += 1

                    yield formatter.write_line(
                        formatter.format_line(token, tags)
                    )

                for reinsertion in sorted(list(sent_reinsertion.keys())):
                    yield formatter.write_line(
                        formatter.format_line(
                            token=sent_reinsertion[reinsertion],
                            tags=[""]*len(tasks)
                        )
                    )

                yield formatter.write_sentence_end()

        if formatter:
            yield formatter.write_footer()
