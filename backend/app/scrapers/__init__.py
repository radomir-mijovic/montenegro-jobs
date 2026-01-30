from .berza_rada import BerzaRada
from .prekoveze import PrekoVeze
from .radnikme import RadnikMe
from .zaposlime import ZaposliMe
from .zzzcg import ZzzCg

SCRAPER_REGISTRY = {
    "prekoveze": PrekoVeze,
    "zaposlime": ZaposliMe,
    "zzzcg": ZzzCg,
    "radnikme": RadnikMe,
    "berzarada": BerzaRada,
}


def get_scraper(scraper: str) -> PrekoVeze | ZaposliMe | ZzzCg:
    """Funciton to initialize and return scraper class

    Args:
        scraper(str): name of the supported scraper

    Returns:
        scraper class or raise a error if source is not supported
    """
    scraper_class = SCRAPER_REGISTRY.get(scraper)
    if not scraper_class:
        raise ValueError(f"Uknown scraper: {scraper}")
    return scraper_class()
