class OneSlowMove(object):
    def __init__(self) -> None:
        self.counter = 0

    def update(self, gameinfo):
        if self.counter > 100:
            self.counter = 0
            src = list(gameinfo._my_planets().values())[0]
            dest = list(gameinfo._not_my_planets().values())[0]
            gameinfo.planet_order(src, dest, src.ships)
            #gameinfo.log("I'll send %d ships from planet %s to planet %s" % (src.ships, src, dest))
        else: 
            self.counter += 1
