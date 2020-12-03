# pie-flask
Flask API for Pie

## How to use :

You can retrieve a Blueprint by using the following code

```python
from flask import Flask
from flask_pie import PieController
from pie_extended.models.fro import get_iterator_and_processor
from pie_extended.cli.sub import get_tagger

app = Flask(__name__)
fro_controller = PieController(
    tagger=get_tagger("fro"),
    get_iterator_and_processor=get_iterator_and_processor,
    path="/fro"
)
fro_controller.init_app(app)

if __name__ == "__main__":
    app.run()
```