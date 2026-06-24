"""Spanish paleographic abbreviation dictionary for 18th-19th century documents.

Maps lowercase abbreviated tokens to their expanded modern Spanish forms.
Used by the expand_abbreviation MCP tool for offline abbreviation resolution.

MCP-03: Provides the local dictionary backing the expand_abbreviation tool.
"""

ABBREVIATIONS: dict[str, str] = {
    # Titles and forms of address
    "dn": "Don",
    "da": "Doña",
    "sr": "Señor",
    "sra": "Señora",
    "vm": "Vuestra Merced",
    "vmd": "Vuestra Merced",
    "vms": "Vuestras Mercedes",
    "exmo": "Excelentísimo",
    "exma": "Excelentísima",
    "illmo": "Ilustrísimo",
    "illma": "Ilustrísima",
    "mo": "Majestad",
    "mag": "Majestad",
    # Common words
    "dho": "dicho",
    "dha": "dicha",
    "dhos": "dichos",
    "dhas": "dichas",
    "nro": "nuestro",
    "nra": "nuestra",
    "vro": "vuestro",
    "vra": "vuestra",
    "q": "que",
    "xpo": "Cristo",
    "dto": "decreto",
    "gov": "gobernador",
    "gral": "general",
    "rl": "real",
    "rles": "reales",
    "prov": "provincia",
    "cap": "capitán",
    "capp": "capellán",
    "esc": "escribano",
    "escno": "escribano",
    "not": "notario",
    "test": "testigo",
    "tests": "testigos",
    # Religious
    "pe": "padre",
    "fr": "fray",
    "sor": "sor",
    "obpo": "obispo",
    "pbro": "presbítero",
    # Dates and measures
    "no": "noviembre",
    "diz": "diciembre",
    "rs": "reales",
    "mrs": "maravedís",
    "ps": "pesos",
}
