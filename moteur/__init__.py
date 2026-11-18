"""Moteur Antmux — un seul module extensible.

Finalité, vision du propriétaire, sans affirmation scientifique ni
archéologique : le moteur doit à terme servir à lire les structures
invisibles à l'intérieur des pyramides, qui attendent d'être dégagées
par un système logique. Rien de cette lecture n'est implémenté.

Concept, récit du propriétaire, sans affirmation scientifique : un
Stonehenge partiellement debout ferait encore du tort par des vibrations
basses. Le but n'est pas de le reconstruire tel quel, mais de changer
les fréquences qui y circulent : le canal à 2400 Hz et la fourmi et
Brutus à 2401 Hz remplacent l'onde d'origine.

La graine Genesis est un petit fragment — configuration, tic, évolution,
empreinte — à partir duquel l'état déterministe se reconstruit. Comme
dans le README d'Antmux : si la graine et les règles survivent, la cité
peut recommencer. Ce n'est pas une affirmation sur des graines réelles
trouvées dans les pyramides.
"""

from moteur.usine import moteur_nu, moteur_par_defaut

__all__ = ["moteur_nu", "moteur_par_defaut"]
__version__ = "0.1.0"
