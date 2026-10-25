# Site-wide switches.

# Images for Insights articles, Briefing items and ASA NEXT (homepage hexagon, cards, image band on item pages).
# False = the site looks exactly as before images were added: logo background in the hexagon,
# striped card placeholders, no image band. The image files and data stay in place.
SHOW_IMAGES = True

# ASA Hexagon page (/hexagon/, /ar/hexagon/). Hidden until the trademark is registered: HEXAGON_PUBLIC stays False
# until Ahmed says so (CLAUDE.md, "ASA Hexagon"). False: the page is not built (its URLs forward to About, noindex),
# the menu items and every link to it are gone, and the name "ASA Hexagon" appears on no other page.
# True: everything comes back exactly as before (page, animation, menu position, links).
HEXAGON_PUBLIC = False

import datetime

# Years of experience on Home, About and Our Team: full years since this date, computed at build time.
EXPERIENCE_SINCE = datetime.date(2005, 8, 15)

def experience_years(today=None):
    today = today or datetime.date.today()
    s = EXPERIENCE_SINCE
    return today.year - s.year - ((today.month, today.day) < (s.month, s.day))
