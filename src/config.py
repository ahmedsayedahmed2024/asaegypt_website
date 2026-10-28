# Site-wide switches.

# Images for Insights articles, Briefing items and ASA NEXT (homepage hexagon, cards, image band on item pages).
# False = the site looks exactly as before images were added: the faint mark in the homepage hexagon,
# the ledger-pattern card placeholders, no image band. The image files and data stay in place.
SHOW_IMAGES = True

# ASA Hexagon page (/hexagon/, /ar/hexagon/). Public since the logo switch (October 2026, trademark applications filed;
# CLAUDE.md, "ASA Hexagon"). False: the page is not built (its URLs forward to About, noindex), the menu items and
# every link to it are gone, and the name "ASA Hexagon" appears on no other page.
# True: the page, its animation, menu position and links.
HEXAGON_PUBLIC = True

import datetime

# Years of experience on Home, About and Our Team: full years since this date, computed at build time.
EXPERIENCE_SINCE = datetime.date(2005, 8, 15)

def experience_years(today=None):
    today = today or datetime.date.today()
    s = EXPERIENCE_SINCE
    return today.year - s.year - ((today.month, today.day) < (s.month, s.day))
