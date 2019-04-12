import re
from flask import Flask
from flask_pie import PieController
from flask_pie.utils import Formatter, MemoryzingTokenizer, DataIterator

model = "/home/thibault/dev/deucalion-model-lasla/model-json.tar"

app = Flask(__name__)


class GlueFormatter(Formatter):
    HEADERS = ["form", "lemma", "POS", "morph", "treated_token"]
    MORPH_PART = ["Case", "Numb", "Deg", "Mood", "Tense", "Voice", "Person"]
    PONCTU = re.compile("\W")

    def __init__(self, tokenizer_memory):
        super(GlueFormatter, self).__init__([])
        self.tokenizer_memory = tokenizer_memory

    def __call__(self, tasks):
        super(GlueFormatter, self).__init__(tasks)
        self.pos_tag = "POS"
        if "POS" not in self.tasks and "pos" in self.tasks:
            self.pos_tag = "pos"
        return self

    def format_headers(self):
        return GlueFormatter.HEADERS

    def format_line(self, token, tags):
        tags = list(tags)
        lemma = tags[self.tasks.index("lemma")]
        print(self.tokenizer_memory.tokens)
        index, input_token, out_token = self.tokenizer_memory.tokens.pop(0)
        if token != out_token:
            print(self.tokenizer_memory.tokens)
            raise Exception("The output token does not match our inputs %s : %s" % (token, out_token))

        if GlueFormatter.PONCTU.match(token):
            return [
                token,
                token,
                "PUNC",
                "MORPH=empty",
                token
            ]

        return [
            input_token,
            lemma.upper().replace("U", "V"),
            tags[self.tasks.index(self.pos_tag)],
            "|".join(
                "{cat}={tag}".format(
                    cat=morph_part,
                    tag=tags[self.tasks.index(morph_part)]
                )
                for morph_part in GlueFormatter.MORPH_PART
                if morph_part in self.tasks and
                tags[self.tasks.index(morph_part)] != "_"
            ) or "MORPH=empty",
            out_token
        ]


# Add the lemmatizer routes
tokenizer = MemoryzingTokenizer()
controller = PieController(model_file=model, headers={"X-Accel-Buffering": "no"},
                           formatter_class=GlueFormatter(tokenizer),
                           iterator=DataIterator(tokenizer=tokenizer))
controller.init_app(app)


if __name__ == "__main__":
    #print(list(tokenizer("Latina qua bella sunt. Sunt bella sumus. jiji")))
    app.run(debug=True)
