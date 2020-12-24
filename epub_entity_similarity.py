import glob
from tqdm import tqdm
import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub
import spacy
import networkx as nx

MAX_DISTANCE = 150
EPUB_PATH = './sink/'
EPUB_GLOB_PATTERN = '*.epub'

FILTERED_ENT_LABELS = ["PERSON", "ORG"]

OUTPUT_GRAPH_FILEPATH = "./graph.gexf"

BOOK_LIST = []

SIMILARITY_THRESHOLD = 0.98

G = nx.Graph()
nlp=spacy.load('en_core_web_md')

def main():
    fetch_books()
    process_books()
    process_graph()
    save_graph()

def fetch_books(path=EPUB_PATH, pattern=EPUB_GLOB_PATTERN, books=BOOK_LIST):
    for filename in glob.glob("{}{}".format(path, pattern)):
        try:
            print("--")
            print("fetch {}".format(filename))
            books.append(epub.read_epub(filename))
        except:
            print("error with this epub")
            pass

def process_books(books=BOOK_LIST):
    for book in books:
        book_to_entities(book)

def process_graph():

    nodes = list(G.nodes(data=True))
    print("Process graph - {} nodes".format(len(nodes)))

    before_filter_count = len(nodes)
    for (n, d) in nodes:
        # remove nodes with weight == 1
        if 'weight' in d and d['weight'] == 1:
            G.remove_node(n)
    print("\t- {} removed".format(before_filter_count - len(G.nodes)))

    nodes = list(G.nodes(data=True))
    before_merge_count = len(nodes)
    for index, (n1, d1) in enumerate(nodes):
        for (n2, d2) in nodes[(index + 1):]:
            try:
                similarity = d1['token'].similarity(d2['token'])
                if similarity > SIMILARITY_THRESHOLD:
                    nx.contracted_nodes(G, n1, n2, True, False)
            except:
                pass
    print("\t- {} similar nodes merges".format(before_merge_count - len(G.nodes)))

def save_graph(graph=G, filepath=OUTPUT_GRAPH_FILEPATH):
    for (n,d) in G.nodes(data=True):

        # delete nlp token attributes
        if "token" in d:
            del d["token"]

        print(d)
        # delete sub-node contractions
        if "contraction" in d:

            # append contraction weight to root node
            for key in d["contraction"]:
                if 'weight' in d["contraction"][key]:
                    d['weight'] += d["contraction"][key]['weight']

            del d["contraction"]

    nx.write_gexf(G, filepath)

def book_to_entities(book):
    items = book.get_items()
    with tqdm(total=len(list(items))) as pbar:
        for item in book.items:
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), features="lxml")
                doc=nlp(soup.get_text())
                previous_ent = None
                for ent in [ent for ent in doc.ents if ent.label_ in FILTERED_ENT_LABELS]:
                    if len(ent.text) > 0:
                        graph_add_node(ent.text, G, ent.label_)
                        if previous_ent:
                            distance = ent.start - previous_ent.end
                            if distance < MAX_DISTANCE:
                                graph_add_edge(ent.text, previous_ent.text, G)
                        previous_ent = ent
            pbar.update(1)

def graph_add_node(label, g, t):
    try:
        node_labels = [d for (n, d) in g.nodes.data('label')]
        node_id = node_labels.index(label)
        g.nodes["n_{}".format(node_id)]['weight']+=1
    except:
        g.add_node(
            "n_{}".format(len(g.nodes) + 1),
            label=label,
            weight=1,
            type=t,
            token= nlp("_".join(label.splitlines()))
        )

def graph_add_edge(label_node_1, label_node_2, g):
    node_labels = [d for (n, d) in g.nodes.data('label')]

    node_index_1 = node_labels.index(label_node_1)
    node_index_2 = node_labels.index(label_node_2)

    if node_index_1 < node_index_2:
        n1 = "n_{}".format(node_index_1)
        n2 = "n_{}".format(node_index_2)
    else:
        n1 = "n_{}".format(node_index_2)
        n2 = "n_{}".format(node_index_1)

    if g.has_edge(n1, n2):
        g[n1][n2]['weight']+=1
    else:
        g.add_edge(n1,n2)
        g[n1][n2]['weight']=1

main()
