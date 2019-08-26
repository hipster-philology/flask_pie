import re
from flask import Flask
from flask_pie import PieController
from flask_pie.utils import Formatter, MemoryzingTokenizer, DataIterator
from flask_pie.formatters.glue import GlueFormatter


model = "/home/thibault/dev/pie/latest-lasla-lat-lemma-2019_08_18-19_45_16.tar"

app = Flask(__name__)


# Add the lemmatizer routes
tokenizer = MemoryzingTokenizer()
controller = PieController(model_file=model, headers={"X-Accel-Buffering": "no"},
                           formatter_class=GlueFormatter(tokenizer),
                           force_lower=True,
                           iterator=DataIterator(tokenizer=tokenizer,
                                                 remove_from_input=DataIterator.remove_punctuation))
controller.init_app(app)


if __name__ == "__main__":
    #print(list(tokenizer("Latina qua bella sunt. Sunt bella sumus. jiji")))
    app.run(debug=True)
