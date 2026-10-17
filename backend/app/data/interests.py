"""Catalogue initial des centres d'intérêt (60 entrées, 10 catégories).

Les `slug` sont immuables : ils servent de clé de jointure et de sélection des icebreakers.
Libellés FR/EN, emoji et ordre d'affichage sont fournis par la base, jamais en dur côté client.
"""

from __future__ import annotations

from typing import Final

# (id, slug, label_fr, label_en, emoji, catégorie, ordre)
CATALOG: Final[tuple[tuple[int, str, str, str, str, str, int], ...]] = (
    (1, "jeux-rpg", "RPG et mondes ouverts", "RPG and open worlds", "🗡️", "Jeux vidéo", 1),
    (2, "jeux-fps", "FPS et compétitif", "FPS and competitive", "🎯", "Jeux vidéo", 2),
    (3, "jeux-coop", "Coopération et survie", "Co-op and survival", "🤝", "Jeux vidéo", 3),
    (4, "jeux-retro", "Rétro et émulation", "Retro and emulation", "🕹️", "Jeux vidéo", 4),
    (5, "jeux-simulation", "Simulation et gestion", "Simulation and management", "🏗️", "Jeux vidéo", 5),
    (6, "jeux-esport", "Esport et stratégie", "Esports and strategy", "🏆", "Jeux vidéo", 6),

    (7, "cinema-sf", "Science-fiction", "Science fiction", "🚀", "Cinéma & Séries", 1),
    (8, "cinema-fantasy", "Fantasy", "Fantasy", "🐉", "Cinéma & Séries", 2),
    (9, "cinema-thriller", "Thriller et polar", "Thriller and crime", "🕵️", "Cinéma & Séries", 3),
    (10, "cinema-animation", "Animation et anime", "Animation and anime", "🎨", "Cinéma & Séries", 4),
    (11, "cinema-docu", "Documentaires", "Documentaries", "🎥", "Cinéma & Séries", 5),
    (12, "cinema-asie", "Cinéma asiatique", "Asian cinema", "🏮", "Cinéma & Séries", 6),

    (13, "musique-rock", "Rock et métal", "Rock and metal", "🎸", "Musique", 1),
    (14, "musique-pop", "Pop et variété", "Pop", "🎤", "Musique", 2),
    (15, "musique-rap", "Rap et hip-hop", "Rap and hip-hop", "🎧", "Musique", 3),
    (16, "musique-electro", "Électro et techno", "Electronic and techno", "🔊", "Musique", 4),
    (17, "musique-jazz", "Jazz et soul", "Jazz and soul", "🎷", "Musique", 5),
    (18, "musique-classique", "Classique et orchestre", "Classical and orchestral", "🎻", "Musique", 6),

    (19, "cuisine-patisserie", "Pâtisserie", "Baking and pastry", "🧁", "Cuisine", 1),
    (20, "cuisine-street", "Street food", "Street food", "🌮", "Cuisine", 2),
    (21, "cuisine-vegan", "Cuisine végétale", "Plant-based cooking", "🥦", "Cuisine", 3),
    (22, "cuisine-grill", "Grillades et BBQ", "Grilling and BBQ", "🍖", "Cuisine", 4),
    (23, "cuisine-vin", "Vins et spiritueux", "Wine and spirits", "🍷", "Cuisine", 5),
    (24, "cuisine-cafe", "Café et thé", "Coffee and tea", "☕", "Cuisine", 6),

    (25, "voyage-villes", "City trips", "City breaks", "🏙️", "Voyage", 1),
    (26, "voyage-nature", "Nature et randos", "Nature and hikes", "🌲", "Voyage", 2),
    (27, "voyage-plage", "Mer et plages", "Sea and beaches", "🏖️", "Voyage", 3),
    (28, "voyage-montagne", "Montagne et ski", "Mountains and skiing", "⛷️", "Voyage", 4),
    (29, "voyage-roadtrip", "Road trips", "Road trips", "🚐", "Voyage", 5),
    (30, "voyage-backpack", "Voyage sac à dos", "Backpacking", "🎒", "Voyage", 6),

    (31, "lecture-fantasy", "Fantasy et SF", "Fantasy and sci-fi", "📚", "Lecture", 1),
    (32, "lecture-policier", "Policier et thriller", "Crime and thriller", "🔍", "Lecture", 2),
    (33, "lecture-romance", "Romance", "Romance", "💌", "Lecture", 3),
    (34, "lecture-manga", "Manga et BD", "Manga and comics", "📖", "Lecture", 4),
    (35, "lecture-essai", "Essais et non-fiction", "Essays and non-fiction", "🧠", "Lecture", 5),
    (36, "lecture-poesie", "Poésie et théâtre", "Poetry and theatre", "🪶", "Lecture", 6),

    (37, "arts-dessin", "Dessin et illustration", "Drawing and illustration", "✏️", "Arts", 1),
    (38, "arts-peinture", "Peinture", "Painting", "🖌️", "Arts", 2),
    (39, "arts-photo", "Photographie", "Photography", "📷", "Arts", 3),
    (40, "arts-theatre", "Théâtre et impro", "Theatre and improv", "🎭", "Arts", 4),
    (41, "arts-danse", "Danse", "Dance", "💃", "Arts", 5),
    (42, "arts-artisanat", "Artisanat et DIY", "Crafts and DIY", "🧶", "Arts", 6),

    (43, "sport-foot", "Football", "Football", "⚽", "Sports", 1),
    (44, "sport-running", "Course à pied", "Running", "🏃", "Sports", 2),
    (45, "sport-velo", "Vélo", "Cycling", "🚴", "Sports", 3),
    (46, "sport-natation", "Natation", "Swimming", "🏊", "Sports", 4),
    (47, "sport-escalade", "Escalade", "Climbing", "🧗", "Sports", 5),
    (48, "sport-yoga", "Yoga et fitness", "Yoga and fitness", "🧘", "Sports", 6),

    (49, "tech-dev", "Développement logiciel", "Software development", "💻", "Technologies", 1),
    (50, "tech-ia", "IA et data", "AI and data", "🤖", "Technologies", 2),
    (51, "tech-opensource", "Open source et Linux", "Open source and Linux", "🐧", "Technologies", 3),
    (52, "tech-domotique", "Domotique et bricolage tech", "Home automation", "🏠", "Technologies", 4),
    (53, "tech-cyber", "Cybersécurité", "Cybersecurity", "🔐", "Technologies", 5),
    (54, "tech-crypto", "Crypto et Web3", "Crypto and Web3", "⛓️", "Technologies", 6),

    (55, "nature-animaux", "Animaux", "Animals", "🐾", "Nature & Animaux", 1),
    (56, "nature-jardin", "Jardinage", "Gardening", "🌱", "Nature & Animaux", 2),
    (57, "nature-ecologie", "Écologie", "Ecology", "♻️", "Nature & Animaux", 3),
    (58, "nature-astro", "Astronomie", "Astronomy", "🔭", "Nature & Animaux", 4),
    (59, "nature-rando", "Randonnée", "Hiking", "🥾", "Nature & Animaux", 5),
    (60, "nature-photo", "Photo nature", "Nature photography", "🌄", "Nature & Animaux", 6),
)

CATEGORIES: Final[tuple[str, ...]] = (
    "Jeux vidéo",
    "Cinéma & Séries",
    "Musique",
    "Cuisine",
    "Voyage",
    "Lecture",
    "Arts",
    "Sports",
    "Technologies",
    "Nature & Animaux",
)
