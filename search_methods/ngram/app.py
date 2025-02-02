import time
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from elasticsearch import Elasticsearch, exceptions
from elasticsearch.helpers import bulk

# Configuración de Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:rootpassword@mysql:3306/dbmalaga'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicialización de la base de datos
db = SQLAlchemy(app)

# Configuración de Elasticsearch
elasticsearch_host = "http://elasticsearch:9200"
es = Elasticsearch(elasticsearch_host)
INDEX_NAME = "pueblos"

# Modelo de la tabla MySQL
class Pueblo(db.Model):
    __tablename__ = 'tbpueblosmalaga'

    SimboloQuimico = db.Column(db.String(2), primary_key=True)
    NombreLocalidad = db.Column(db.String(30), unique=True, nullable=True)
    Comarca = db.Column(db.String(30))
    AlturaNivelMar = db.Column(db.Integer)
    Habitantes = db.Column(db.Integer)
    Superficie = db.Column(db.DECIMAL(4, 1))
    NumeroElementoQuimico = db.Column(db.Integer, unique=True)
    Escudo = db.Column(db.LargeBinary)

    def to_dict(self):
        return {
            "SimboloQuimico": self.SimboloQuimico,
            "NombreLocalidad": self.NombreLocalidad,
            "Comarca": self.Comarca,
            "AlturaNivelMar": self.AlturaNivelMar,
            "Habitantes": self.Habitantes,
            "Superficie": str(self.Superficie if self.Superficie is not None else 0),
            "NumeroElementoQuimico": self.NumeroElementoQuimico,
        }

# Verificar conexión a Elasticsearch con pausas
def connect_to_elasticsearch():
    print("Iniciando conexión a Elasticsearch...")
    for attempt in range(20):
        try:
            if es.ping():
                print("Conectado a Elasticsearch")
                return
            print(f"Intento {attempt + 1}: Elasticsearch no está disponible. Reintentando...")
        except exceptions.ConnectionError as e:
            print(f"Error de conexión: {e}. Reintentando...")
        time.sleep(5)
    print("No se pudo conectar a Elasticsearch después de varios intentos.")
    exit(1)

# Crear el índice en Elasticsearch si no existe, con análisis n-gram
def create_index():
    print("Verificando si el índice existe...")

    mappings = {
        "settings": {
            "index": {
                "max_ngram_diff": 8  # Permite una diferencia de 8 entre max_gram y min_gram
            },
            "analysis": {
                "tokenizer": {
                    "ngram_tokenizer": {
                        "type": "ngram",
                        "min_gram": 2,
                        "max_gram": 10,  # Permitido gracias a max_ngram_diff
                        "token_chars": ["letter", "digit"]
                    }
                },
                "analyzer": {
                    "ngram_analyzer": {
                        "type": "custom",
                        "tokenizer": "ngram_tokenizer",
                        "filter": ["lowercase"]
                    },
                    "standard_analyzer": {
                        "type": "standard"
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "SimboloQuimico": {"type": "keyword"},
                "NombreLocalidad": {
                    "type": "text",
                    "analyzer": "ngram_analyzer",
                    "search_analyzer": "standard_analyzer"
                },
                "Comarca": {
                    "type": "text",
                    "analyzer": "ngram_analyzer",
                    "search_analyzer": "standard_analyzer"
                },
                "AlturaNivelMar": {"type": "integer"},
                "Habitantes": {"type": "integer"},
                "Superficie": {"type": "float"},
                "NumeroElementoQuimico": {"type": "integer"},
                "Escudo": {"type": "binary"},
            }
        }
    }

    if not es.indices.exists(index=INDEX_NAME):
        print(f"El índice '{INDEX_NAME}' no existe. Intentando crearlo...")
        try:
            es.indices.create(index=INDEX_NAME, body=mappings)
            print(f"Índice '{INDEX_NAME}' creado con éxito.")
        except Exception as e:
            print(f"Error al crear el índice '{INDEX_NAME}': {e}")
            exit(1)
    else:
        print(f"El índice '{INDEX_NAME}' ya existe.")

# Indexar los datos en Elasticsearch
def index_data():
    print("Comenzando el proceso de indexación...")
    pueblos = Pueblo.query.all()
    if not pueblos:
        print("No se encontraron pueblos en la base de datos.")
        return

    actions = []
    for pueblo in pueblos:
        action = {
            "_index": INDEX_NAME,
            "_id": pueblo.SimboloQuimico,
            "_source": pueblo.to_dict(),
        }
        actions.append(action)

    try:
        success, failed = bulk(es, actions, raise_on_error=False)
        print(f"Indexados {success} documentos con éxito.")
        if failed:
            print(f"{len(failed)} documentos fallaron.")
    except Exception as e:
        print(f"Error en el proceso de indexación: {e}")

# Ruta de búsqueda en Flask
@app.route('/search', methods=['GET'])
def search_pueblos():
    print("Buscando pueblos en Elasticsearch...")
    query = request.args.get('q', '')
    if not query:
        return jsonify({"error": "Por favor, proporciona un término de búsqueda."}), 400

    body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["NombreLocalidad", "Comarca"],
                "operator": "and"
            }
        }
    }

    try:
        results = es.search(index=INDEX_NAME, body=body)
        pueblos = [{"id": hit["_id"], **hit["_source"]} for hit in results["hits"]["hits"]]
        return jsonify(pueblos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    connect_to_elasticsearch()
    time.sleep(5)
    create_index()
    time.sleep(5)
    with app.app_context():
        index_data()
        time.sleep(5)
    app.run(debug=True, host='0.0.0.0')
