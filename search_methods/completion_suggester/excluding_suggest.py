
        "mappings": {
            "_source": {  # Agregar esto para ocultar "suggest"
                "excludes": ["suggest"]
            },
            "properties": {
                "SimboloQuimico": {"type": "keyword"},
                "NombreLocalidad": {"type": "text"},
                "Comarca": {"type": "text"},
                "AlturaNivelMar": {"type": "integer"},
                "Habitantes": {"type": "integer"},
                "Superficie": {"type": "float"},
                "NumeroElementoQuimico": {"type": "integer"},
                "Escudo": {"type": "binary"},
                "suggest": {
                    "type": "completion"
                }
            }
        }
    }
