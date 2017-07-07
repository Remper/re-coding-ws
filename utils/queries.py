SMT_API_BASE = "http://api.smt.futuro.media/"
KNOWLEDGE_BASE_API = "http://ganymede.fbk.eu/dbpedia2/sparql"
SMT_API = SMT_API_BASE + "alignments/by_twitter_id"
SMT_API_SIMILARITY = SMT_API_BASE + "annotate/is_similar"
SMT_API_RECODE_FRIENDS = SMT_API_BASE + "recode/friends"

RESOURCE_QUERY = '''
    SELECT
        ?relation ?property
    WHERE {
        ?property ?relation <http://en.wikipedia.org/wiki/:id>
    }
    GROUP BY ?property ?relation
'''

RESOURCES_BY_NAME_QUERY = '''
    PREFIX foaf:  <http://xmlns.com/foaf/0.1/>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT ?agent
    WHERE {
        ?agent rdf:type <http://dbpedia.org/ontology/Agent> .
        ?agent foaf:name ?n .
        ?n bif:contains '":res_name"'
    }
    GROUP BY ?agent
'''