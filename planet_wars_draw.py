from entities import NEUTRAL_ID
import pyglet

COLOR_NAMES = {
	"BLACK": (0.0, 0.0, 0.0, 1),
	"WHITE": (1.0, 1.0, 1.0, 1),
	"RED": (1.0, 0.0, 0.0, 1),
	"GREEN": (0.0, 1.0, 0.0, 1),
	"BLUE": (0.0, 0.0, 1.0, 1),
	"GREY": (0.6, 0.6, 0.6, 1),
	"PINK": (1.0, 0.7, 0.7, 1),
	"YELLOW": (1.0, 1.0, 0.0, 1),
	"ORANGE": (1.0, 0.7, 0.0, 1),
	"PURPLE": (1.0, 0.0, 0.7, 1),
	"BROWN": (0.5, 0.35, 0.0, 1),
	"AQUA": (0.0, 1.0, 1.0, 1),
	"DARK_GREEN": (0.0, 0.4, 0.0, 1),
	"LIGHT_BLUE": (0.6, 0.6, 1.0, 1),
	"LIGHT_GREY": (0.9, 0.9, 0.9, 1),
	"LIGHT_RED": (1.0, 0.6, 0.6, 1),
	"LIGHT_GREEN": (0.6, 1.0, 0.6, 1),
}


def to_rgb(a_gl_color):
	return tuple([int(x * 255) for x in a_gl_color])


COLOR_NAMES_255 = {k: to_rgb(v) for k, v in COLOR_NAMES.items()}

IMAGES = {
	"background": "images/space.jpg",
}

class RenderablePlanet:
	def __init__(self, planet):
		pass

class RenderableFleet:
	def __init__(self, planet):
		pass

class PlanetWarsEntityRenderer:
	# handles drawing/cached pos/size of PlanetWars game instance for a GUI

	def __init__(self, game, window):
		self.game = game
		#set the playour colours
		self.playercolours = {}
		for p in game.players:
			#players can't be BLACK or WHITE
			for k in list(COLOR_NAMES.keys())[2:]:
				#colours must be unique
				if k not in self.playercolours.values():
					self.playercolours[p] = k

	def draw(self):
		# draw planets
		for p in self.game.planets.values():
			pyglet.shapes.circle(p.pos, p.radius, color=p.color, filled=True)
			pyglet.shapes.circle(p.pos, p.radius, color=COLOR_NAMES["WHITE"], filled=False)
			if p.owner != NEUTRAL_ID:  # 0 == neutral_id
				pyglet.shapes.circle(p.pos, p.view_radius, color=p.color, filled=False)
			
			p.label.draw()
		# draw fleets
		for f in self.game.fleets.values():
			self.pyglet.shapes(f.pos, f.radius, color=f.color, filled=False)
			f.label.draw()

	def sync_all(self, view_id=0, label_type="ships"):
		# todo: only need to update label values and owner colour details of planets
		# recache all planets/fleets
		if view_id == 0:
			planets = self.game.planets
			fleets = self.game.fleets
		else:
			planets = self.game.players[view_id].planets
			fleets = self.game.players[view_id].fleets

		# Set which label_type detail to show (id, num_ships, vision etc)
		for k, p in planets.items():
			self.planets[k] = self._planet_stamp(p, p.__getattribute__(label_type))

		self.fleets.clear()
		for k, f in fleets.items():
			self.fleets[k] = self._fleet_stamp(f, f.num_ships)

	def _planet_stamp(self, planet, value):
		pos = self.game_to_screen(planet.x, planet.y)
		radius = (self.ratio * PLANET_MIN_R) + (
			(PLANET_FACTOR * self.ratio) * planet.growth_rate
		)
		view_radius = planet.vision_range() * self.ratio
		color = COLOR[planet.owner_id]
		label = Label(
			str(value),
			color=COLOR_NAMES_255["BLACK"],
			x=pos[0],
			y=pos[1],
			anchor_x="center",
			anchor_y="center",
		)
		return ScreenPlanet(pos, planet.owner_id, radius, view_radius, color, label)

	def _fleet_stamp(self, fleet, value):
		pos = self.game_to_screen(fleet.x, fleet.y)
		radius = 20.0
		view_radius = fleet.vision_range() * self.ratio
		color = COLOR[fleet.owner_id]
		label = Label(
			str(value),
			color=COLOR_NAMES_255["WHITE"],
			x=pos[0],
			y=pos[1],
			anchor_x="center",
			anchor_y="center",
		)
		return ScreenFleet(pos, fleet.owner_id, radius, view_radius, color, label)

	def game_to_screen(self, wx, wy):
		# convert xy values from game space to screen space
		x = ((wx - self.min_x) / self.dx) * self.display_dx + self.margin
		y = ((wy - self.min_y) / self.dy) * self.display_dy + self.margin
		return (x, y)


class PlanetWarsUI:
	def __init__(self, window):
		self.label_type = "num_ships"
		self.fps_display = pyglet.window.FPSDisplay(window)
		self.step_label = pyglet.text.Label(
			"STEP", x=5, y=window.height - 20, color=COLOR_NAMES_255["WHITE"]
		)

	def draw(self):
		self.fps_display.draw()
		self.step_label.draw()


class PlanetWarsWindow(pyglet.window.Window):
	def __init__(self, game):
		#init the Pyglet window
		super(PlanetWarsWindow, self).__init__(
			game.extent["w"],
			game.extent["h"],
			vsync=True,
			resizable=False,
			caption="Planet Wars",
		)
		#set our location on the screen
		#we use game.extent directly to set screen size opn the previous line,
		#and it's not resizable, so we want it pretty high on the screen
		#essentially there's a 1:1 map between screen size and map size that can be displayed
		self.set_location(10, 10)
		
		#load the background and scale it to the widnow size
		self.bg = pyglet.sprite.Sprite(pyglet.image.load(".\\images\\space.jpg"))
		self.bg.scale_x = self.width / self.bg.image.width
		self.bg.scale_y = self.height / self.bg.image.height
		#load the global UI elements (FPS counter, etc.)
		self.ui = PlanetWarsUI(self)
		#load the renderer for game elements
		self.gamerenderer = PlanetWarsEntityRenderer(game, self)

		# pyglet.clock.schedule_interval(game.update, 1/60.)
		pyglet.app.run()

	def reset_space(self):
		self.adaptor.screen_resize(self.width, self.height)
		self.adaptor.sync_all(self.view_id, self.label_type)

	def update(self, args):
		# gets called by the scheduler at the step_fps interval set
		game = self.game
		if game:
			if not self.paused:
				game.update()
				self.adaptor.sync_all()

			# update step label
			msg = "Step:" + str(game.tick)
			if self.paused:
				msg += " [PAUSED]"
			msg += ", View:" + str(self.view_id)
			if self.view_id in game.players:
				msg += " " + game.players[self.view_id].name
			elif self.view_id == 0:
				msg += " All "
			msg += str(game.tick)
			msg += " Show: " + self.label_type

			self.step_label.text = msg
			# Has the game ended? (Should we close?)
			if not self.game.is_alive() or self.game.tick >= self.max_tick:
				self.close()
		else:
			self.step_label.text = "---"

	def set_pen_color(self, color=None, name=None):
		if name is not None:
			color = COLOR_NAMES[name]
		self.curr_color = color
		glColor4f(*self.curr_color)

	def set_stroke(self, stroke):
		self.stroke = stroke
		glLineWidth(self.stroke)

	def circle(self, pos, radius, color=None, filled=True):
		if color:
			self.set_pen_color(color)
		if filled:
			gluQuadricDrawStyle(self.qobj, GLU_FILL)
		else:
			gluQuadricDrawStyle(self.qobj, GLU_SILHOUETTE)
		glPushMatrix()
		glTranslatef(pos[0], pos[1], 0.0)
		gluDisk(self.qobj, 0, radius, 32, 1)
		glPopMatrix()

	def line(self, x1=0, y1=0, x2=0, y2=0, pos1=None, pos2=None):
		"""Draw a single line. Either with xy values, or two position (that
		contain x and y values). Uses existing colour and stroke values."""
		if pos1 is not None and pos2 is not None:
			x1, y1, x2, y2 = pos1[0], pos1[1], pos2[0], pos2[1]
		glBegin(GL_LINES)
		glVertex2f(x1, y1)
		glVertex2f(x2, y2)
		glEnd()

	def on_key_press(self, symbol, modifiers):
		# Single Player View, or All View
		if symbol == key.BRACKETLEFT:
			self.view_id = (
				self.view_id - 1 if self.view_id > 1 else len(self.game.players)
			)
		if symbol == key.BRACKETRIGHT:
			self.view_id = (
				self.view_id + 1 if self.view_id < len(self.game.players) else 1
			)
		# Everyone view
		elif symbol == key.A:
			self.view_id = 0  # == "all"
		# Planet attribute type to show?
		elif symbol == key.L:
			i = self.label_type
			l = ["id", "num_ships", "vision_age", "owner_id"]
			self.label_type = l[l.index(i) + 1] if l.index(i) < (len(l) - 1) else l[0]
		# Reset?
		elif symbol == key.R:
			self.reset_space()
		# Do one step
		elif symbol == key.N:
			self.game.update()
		# Pause toggle?
		elif symbol == key.P:
			self.paused = not self.paused
		# Speed up (+) or slow down (-) the sim
		elif symbol in [key.PLUS, key.EQUAL]:
			self.set_fps(self.fps + 5)
		elif symbol == key.MINUS:
			self.set_fps(self.fps - 5)

		self.adaptor.sync_all(self.view_id, self.label_type)

	def on_draw(self):
		self.clear()
		self.bg.draw()
		self.ui.draw()
		self.gamerenderer.draw()