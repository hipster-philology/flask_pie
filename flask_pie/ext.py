from flask import Blueprint, request, Flask, Response, stream_with_context
from werkzeug.exceptions import BadRequest
from typing import Iterator

from pie_extended.tagger import ExtensibleTagger
from pie_extended.pipeline.postprocessor.proto import ProcessorPrototype
from pie_extended.pipeline.iterators.proto import DataIterator
from pie_extended.pipeline.formatters.proto import Formatter


from typing import Callable, Tuple, Type


class PieController(object):
    def __init__(self,
                 tagger: ExtensibleTagger,
                 get_iterator_and_processor: Callable[[], Tuple[DataIterator, ProcessorPrototype]],
                 path: str = "/api",
                 name: str = "nlp_pie",
                 batch_size: int = None,
                 formatter_class: Type[Formatter] = Formatter,
                 headers=None, force_lower=False):

        self._bp: Blueprint = Blueprint(name, import_name=name, url_prefix=path)
        self.force_lower = force_lower
        self.tagger = tagger
        self.get_iterator_and_processor = get_iterator_and_processor
        self.batch_size = batch_size
        self.tagger.batch_size = batch_size or 8
        self.formatter = formatter_class
        self.headers = {
            'Content-Type': 'text/plain; charset=utf-8',
            'Access-Control-Allow-Origin': "*"
        }
        if isinstance(headers, dict):
            self.headers.update(headers)

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

        if lower:
            data = data.lower()

        if not data:
            raise BadRequest()
        else:
            iter_fn, proc = self.get_iterator_and_processor()
            yield from self.tagger.iter_tag(
                data=data,
                formatter_class=self.formatter,
                iterator=iter_fn,
                processor=proc
            )
