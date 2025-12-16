from enum import Enum


class EtatRessource(Enum):
    active = "active"
    en_maintenance = "en maintenance"
    hors_service = "hors service"