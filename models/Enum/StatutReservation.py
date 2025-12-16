from enum import Enum


class StatutReservation(Enum):
    en_cours = "en cours"
    confirme = "confirme"
    annule = "annule"
    fini = "fini"
    non_present = "non present"