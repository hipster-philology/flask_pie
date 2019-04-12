from flask import Blueprint, request, Flask, Response, stream_with_context
from typing import Iterator
from pie.tagger import Tagger
from pie.utils import chunks, model_spec


from .utils import DataIterator, Tokenizer, Formatter


class PieController(object):
    def __init__(self,
                 path: str = "/api", name: str = "nlp_pie", iterator: DataIterator=None, device: str = None,
                 batch_size: int = None, model_file: str = None, formatter_class: Formatter = None,
                 headers = None):

        self._bp: Blueprint = Blueprint(name, import_name=name, url_prefix=path)
        self.tokenizer: Tokenizer = None
        self.formatter_class = formatter_class or Formatter
        self.batch_size = batch_size
        self.model_file = model_file
        self.headers = {
            'Content-Type': 'text/plain; charset=utf-8',
            'Access-Control-Allow-Origin': "*"
        }
        if isinstance(headers, dict):
            self.headers.update(headers)

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
            header = False
            for chunk in chunks(self.iterator(data, lower=lower), size=self.batch_size):
                sents, lengths = zip(*chunk)

                tagged, tasks = self.tagger.tag(sents=sents, lengths=lengths)
                formatter = self.formatter_class(tasks)
                sep = "\t"
                for sent in tagged:
                    if not header:
                        yield sep.join(formatter.format_headers()) + '\r\n'
                        header = True
                    for token, tags in sent:
                        yield sep.join(formatter.format_line(token, tags)) + '\r\n'
