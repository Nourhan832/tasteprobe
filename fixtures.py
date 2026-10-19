"""Invented affinities for testing. Film metadata is editorial, not Qloo output."""
FILMS = [
    ("arrival", "Arrival", "Science fiction · 2016", "A linguist searches for meaning in an encounter with visitors from another world."),
    ("amelie", "Amélie", "Romance · 2001", "A playful portrait of small kindnesses and an imaginative life in Paris."),
    ("whiplash", "Whiplash", "Drama · 2014", "A young drummer faces the cost of ambition and an exacting mentor."),
    ("her", "Her", "Science fiction · 2013", "A quiet exploration of intimacy, technology, and human connection."),
    ("spirited", "Spirited Away", "Animation · 2001", "A young girl enters an extraordinary world of spirits and transformation."),
    ("moonrise", "Moonrise Kingdom", "Adventure · 2012", "Two young runaways create a world of their own."),
    ("interstellar", "Interstellar", "Science fiction · 2014", "A journey across space entwines scientific ambition and family bonds."),
    ("grand", "The Grand Budapest Hotel", "Comedy · 2014", "A meticulously styled caper through a changing Europe."),
    ("soul", "Soul", "Animation · 2020", "A jazz musician reconsiders what makes a life meaningful."),
]
METADATA = {i: {"entity_id": i, "name": n, "subtitle": s, "description": d} for i, n, s, d in FILMS}
PROFILES = {
    "Reflective worlds": dict(zip(METADATA, [.9, .35, .3, .95, .7, .6, .8, .4, .65])),
    "Playful imagination": dict(zip(METADATA, [.35, .95, .25, .6, .8, .9, .3, .95, .6])),
    "Rhythm & intensity": dict(zip(METADATA, [.4, .3, .95, .3, .6, .4, .85, .5, .95])),
}
