# Epub Entity similarity to gexf

Build graph based on nlp entities found in multiple epub files.

![Screenshot](screenshot.png?raw=true "Screenshot")

## Requirements

``` sh
git clone https://github.com/alx/epub_entity_similarity.git
cd epub_entity_similarity

source bin/activate
pip install -r requirements.txt
```

# Usage

``` sh
# Copy epub files in ./sink/
python epub_entity_similarity.py

# open graph.gexf with gephi - https://gephi.org/users/download/
```
