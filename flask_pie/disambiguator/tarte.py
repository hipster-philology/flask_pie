from tarte.tagger import Tagger

from .proto import Disambiguator


class TarteDisambiguator(Disambiguator):
    def __init__(self, model_path, device="cpu", formatter=None):
        self.model = Tagger(model_path)
        self.model.use_device(device)
        self.formatter = formatter or Tagger.formatter

    def __call__(self, sent, tasks):
        reformated = [
            [lemma, tags[tasks.index("lemma")], tags[tasks.index("pos")]]
            for lemma, tags in sent
        ]
        sentence = []
        tagged = self.model.tag([reformated], formatter=self.formatter)

        for (tok, tags), new_lemma in zip(sent, next(tagged)):
            tags = list(tags)
            tags[tasks.index("lemma")] = new_lemma
            sentence.append((tok, tuple(tags)))
        return sentence
