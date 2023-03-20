import copy
import collections
from entities import Planet, Fleet, NEUTRAL_ID
from players import Player
from planet_wars_draw import PLANET_RADIUS_FACTOR


class PlanetWarsGame():

	def __init__(self, gamestate_json):
		self.planets = {}
		for p in gamestate_json['planets']:
			p = Planet(
				p['x'],
				p['y'],
				p.get('ID'),
				p.get('owner'),
				p.get('ships'),
				p.get('growth')
			)
			self.planets[p.ID] = p
		self.fleets = {}
		if 'fleets' in gamestate_json:
			for f in gamestate_json['fleets']:
				f = Fleet(f)
				self.fleets[f.ID] = f
		if 'orders' in gamestate_json:
			self.orders = gamestate_json['orders']
		if 'players' in gamestate_json:
			self.players = {}
			self.players[NEUTRAL_ID] = Player(NEUTRAL_ID, "Neutral") 
			for p in gamestate_json['players']:
				self.players[p["ID"]] = Player(p["ID"], p["name"])

		self.spawn_players()
		#set initial facades
		for player in self.players.values():
			if player.ID != NEUTRAL_ID:
				self.update_facade(player)

		self.tick = 0
		self.max_tick = 1000
		self.winner = None
		self.dirty = True
		self.paused = True

	def spawn_players(self):
		players_to_be_spawned = []
		planets_by_player = collections.defaultdict(list) #should we keep this on self as a speedy cache and just move planets around when they change hands?
		centroid_of_owned_planets = [0,0]
		sum_of_owned_planets = [0,0]
		sum_of_planets = [0, 0]
		count_of_owned_planets = 0
		for player in self.players.values():
			for planet in self.planets.values():
				sum_of_planets[0] += planet.x
				sum_of_planets[1] += planet.y
				if planet.owner == player.ID:
					planets_by_player[player.ID].append(planet)
					sum_of_owned_planets[0] += planet.x
					sum_of_owned_planets[1] += planet.y
					count_of_owned_planets += 1
			if not player.ID in planets_by_player.keys():
				players_to_be_spawned.append(player.ID)
		unowned_planets = planets_by_player.pop(NEUTRAL_ID)
		#quick check that we have enough planets for players
		if len(players_to_be_spawned) > len(unowned_planets):
			raise ValueError("Not enough planets for players to spawn")
		for playerID in players_to_be_spawned:
			if count_of_owned_planets == 0:
				centroid_of_owned_planets[0] = sum_of_planets[0]/count_of_owned_planets
				centroid_of_owned_planets[1] = sum_of_planets[0]/count_of_owned_planets
			else:
				centroid_of_owned_planets[0] = sum_of_owned_planets[0]/count_of_owned_planets
				centroid_of_owned_planets[1] = sum_of_owned_planets[1]/count_of_owned_planets
			dist = 0
			candidate = None
			for planet in unowned_planets:
				_dist = planet.distance_to(
					x=centroid_of_owned_planets[0], 
					y=centroid_of_owned_planets[1]
				)
				if _dist > dist:
					candidate = planet
					dist = _dist
			candidate.owner = playerID
			unowned_planets.remove(candidate)
			sum_of_owned_planets[0] += candidate.x
			sum_of_owned_planets[1] += candidate.y
			count_of_owned_planets += 1
			#if we use planets_by_player again, be sure to set it up here

	# adds target to an entity dict (defaults to deepcopy) 
	# if it is in vision_range of src
	# does not add if:
	#	- they have the same owner (force param overrides this behaviour)
	#	- target already exists in entity_list
	def add_to_vision_list(self, src, target, entity_dict, force=False, shallowcpy=False):
		if shallowcpy:
			_copy = copy.copy
		else:
			_copy = copy.deepcopy
		#obviously it can see other entities owned by the same player
		if src.owner == target.owner:
			if force:
				entity_dict[target.ID] = _copy(target)
			return
		
		#skip planets that have already be seen by something else
		if target.ID not in entity_dict.facade.planets or force:
			#check vision range and add if visible
			if src.distance_to(target) < src.vision_range()**2:
				entity_dict[target.ID] == copy.deepcopy(target)

	def update_facade(self, player):
		if len(player.planets) == 0:
			#player starts the game with knowledge of the inital state of all planets
			#TODO: this shouldn't be the case if the game is loaded from a later state
			player.planets = copy.deepcopy(self.planets)
		else:
			for planet in self.planets.values():
				if planet.owner == player.ID:
					#you can see a planet if you own it
					player.planets[planet.ID] == copy.deepcopy(planet)
				else:
					#check what other planets this planet can see
					for other in self.planets.values():
						self.add_to_vision_list(planet, other, player.planets)
					#same logic, but for fleets
					for other in self.fleets.values():
						self.add_to_vision_list(planet, other, player.fleets)

		player.fleets = {} #no memory of fleets last locations
		for fleet in self.fleets.values():
			if fleet.owner == player.ID:
				#you can see a fleet if you own it
				player.planets[planet.ID] == copy.deepcopy(planet)
			else:
				#check what other planets this fleet can see
				for other in self.planets.values():
					self.add_to_vision_list(fleet, other, player.planets)
				#same logic, but for fleets
				for other in self.fleets.values():
					self.add_to_vision_list(fleet, other, player.fleets)

	#def __str__(self):
	#	# todo: this doesn't match the _parse_gamestate_text format anymore
	#	s = []
	#	s.append("M %d %d %d %d" %
	#			 (self.gameid, self.player_id, self.tick, self.winner.id))
	#	for p in self.planets:
	#		s.append("P %f %f %d %d %d" % (p.x, p.y, p.owner_id, p.ships, p.growth_rate))
	#	for f in self.fleets:
	#		s.append("F %d %d %d %d %d %d" % (f.owner_id, f.ships, f.src, f.dest,
	#										  f.total_trip_length, f.turns_remaining))
	#	return "\n".join(s)

	def update(self, t=None):
		# phase 0, Give each player (controller) a chance to create new fleets
		for player in self.players.values():
			player.update()
		# phase 1, Retrieve and process all pending orders from each player
		for player in self.players.values():
			self._process_orders(player)
		# phase 2, Planet ship number growth (advancement)
		for planet in self.planets.values():
			planet.update()
		# phase 3, Update fleets, check for arrivals
		arrivals = collections.defaultdict(list)
		for f in self.fleets.values():
			f.update()
			if f.distance_to(f.dest) <= PLANET_RADIUS_FACTOR:
				arrivals[f.dest].append(f)
		# phase 4, Collate fleet arrivals and planet forces by owner
		for p, fleets in arrivals.items():
			forces = collections.defaultdict(int)
			# add the current occupier of the planet
			forces[p.owner_id] = p.ships
			# add arriving fleets
			for f in fleets:
				self.fleets.pop(f.id)
				forces[f.owner_id] += f.ships
			# Simple reinforcements?
			if len(forces) == 1:
				p.ships = forces[p.owner_id]
			# Battle!
			else:
				# There are at least 2 forces, maybe more. Biggest force is winner.
				# Gap between 1st and 2nd is the remaining force. (The rest cancel each out.)
				result = sorted([(v, k) for k, v in forces.items()], reverse=True)
				winner_id = result[0][1]
				gap_size = result[0][0] - result[1][0]
				# If meaningful outcome, log it
				if winner_id == 0:  # neutral defense - log nothing
					pass
				elif winner_id == p.owner_id:
					self.turn_log(
						"{0:4d}: Player {1} defended planet {2}".format(self.tick, winner_id, p.id))
				else:
					self.turn_log(
						"{0:4d}: Player {1} now owns planet {2}".format(self.tick, winner_id, p.id))
					#if the planet changed hands, we have to change how it is rendered
					self.dirty = True
				# Set the new winner
				p.owner_id = winner_id
				p.ships = gap_size
				p.was_battle = True
		# phase 5, Update the game tick count.
		self.tick += 1
		# phase 6, Resync current facade view of the map for each player
		for player in self.players.values():
			pass
			#self._sync_player_view(player)

	def _sync_player_view(self, player):
		player.tick = self.tick
		# find out which planets / fleets are currently in view
		planetsinview = set()
		fleetsinview = set()
		for planet in self.planets.values():
			if planet.owner == player.ID:
				planetsinview.update(planet.in_range(self.planets.values()))
				fleetsinview.update(planet.in_range(self.fleets.values()))
		for fleet in self.fleets.values():
			# ignore old fleets
			if (fleet.owner_id == player.id) and (fleet.id in self.fleets):
				planetsinview.update(fleet.in_range(self.planets.values()))
				fleetsinview.update(fleet.in_range(self.fleets.values()))

		# update (recopy) new details for all planets in view
		# Increase vision_age of planets that are no longer in view
		for p_id, planet in player.planets.items():
			if p_id in planetsinview:
				player.planets[p_id] = self.planets[p_id].copy()
				player.planets[p_id].vision_age = 0
			else:
				if planet.owner_id == player.id:  # lost planet?
					# let player know winner
					planet.owner_id = self.planets[p_id].owner_id
				planet.vision_age += 1
		# clear old fleet list, (if they aren't in view they disappear), copy in view
		player.fleets.clear()
		for f_id in fleetsinview:
			player.fleets[f_id] = self.fleets[f_id].copy()
		# get the player to update their gameinfo with new details
		player.refresh_gameinfo()

	def _process_orders(self, player):
		''' Process all pending orders for the player, then clears the orders.
			An order sends ships from a player-owned fleet or planet to a planet.

			Checks for valid order conditions:
			- Valid source src (planet or fleet)
			- Valid destination dest (planet only)
			- Source is owned by player
			- Source has ships to launch (>0)
			- Limits number of ships to number available

			Invalid orders are modfied (ship number limit) or ignored.
		'''
		for order in player.orders:
			o_type, src_id, new_id, ships, dest_id = order
			# Check for valid fleet or planet id?
			if src_id not in (self.planets.keys() | self.fleets.keys()):
				self.turn_log("Invalid order ignored - not a valid source.")
			# Check for valid planet destination?
			elif dest_id not in self.planets:
				self.turn_log("Invalid order ignored - not a valid destination.")
			else:
				# Extract and use the src and dest details
				src = self.fleets[src_id] if o_type == 'fleet' else self.planets[src_id]
				dest = self.planets[dest_id]
				# Check that player owns the source of ships!
				if src.owner is not player.ID:
					self.turn_log("Invalid order ignored - player does not own source!")
				# Is the number of ships requested valid?
				if ships > src.ships:
					self.turn_log("Invalid order modified - not enough ships. Max used.")
					ships = src.ships
				# Still ships to launch? Do it ...
				if ships > 0:
					fleet = Fleet(new_id, player.ID, ships, src, dest)
					src.remove_ships(ships)
					# old empty fleet removal
					if o_type == 'fleet' and src.ships == 0:
						del self.fleets[src.id]
					# keep new fleet
					self.fleets[new_id] = fleet
					msg = "{0:4d}: Player {1} launched {2} (left {3}) ships from {4} {5} to planet {6}".format(
						self.tick, player.ID, ships, src.ships, o_type, src.ID, dest.ID)
					self.turn_log(msg)
					#player.log(msg)
					self.dirty = True
				else:
					self.turn_log("Invalid order ignored - no ships to launch.")
		# Done - clear orders.
		# Why not use pop?
		player.orders[:] = []

	def is_alive(self):
		''' Return True if two or more players are still alive. '''
		#why are we asking the players if they're alive?
		#status = [p for p in self.players.values() if p.is_alive()]
		#if len(status) == 1:
		#	self.winner = status[0]
		#	return False
		#else:
		#	return True
		return True

	def turn_log(self, msg):
		pass