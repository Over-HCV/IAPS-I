from mesa.examples.advanced.alliance_formation.model import MultiLevelAllianceModel
from mesa.examples.advanced.epstein_civil_violence.model import EpsteinCivilViolence
from mesa.examples.advanced.pd_grid.model import PdGrid
from mesa.examples.advanced.sugarscape_g1mt.model import SugarscapeG1mt
from mesa.examples.advanced.wolf_sheep.model import WolfSheep
from mesa.examples.basic.boid_flockers.model import BoidFlockers
from mesa.examples.basic.boltzmann_wealth_model.model import BoltzmannWealth
from mesa.examples.basic.conways_game_of_life.model import ConwaysGameOfLife
from mesa.examples.basic.schelling.model import Schelling
from mesa.examples.basic.virus_on_network.model import VirusOnNetwork

# El tram_model vive en mesa.examples.experimental, que solo existe en Mesa 4.x. El
# entorno usa Mesa 3.5.1, donde mesa.examples solo trae `basic` y `advanced`, así que el
# import se hace tolerante en vez de romper todo el paquete.
try:
    from mesa.examples.experimental.tram_model.model import TransitSystem
except ModuleNotFoundError:  # pragma: no cover - depende de la versión de Mesa
    TransitSystem = None  # type: ignore[assignment,misc]

__all__ = [
    "BoidFlockers",
    "BoltzmannWealth",
    "ConwaysGameOfLife",
    "EpsteinCivilViolence",
    "MultiLevelAllianceModel",
    "PdGrid",
    "Schelling",
    "SugarscapeG1mt",
    "TransitSystem",
    "VirusOnNetwork",
    "WolfSheep",
]
