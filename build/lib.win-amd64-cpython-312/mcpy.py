import math
import random
from cProfile import Profile
import pyglet

pyglet.options["shadow_window"] = False
pyglet.options["debug_gl"] = False

import pyglet.gl as gl
import pyglet.window.mouse

from src.entity.player import SPRINTING_SPEED, WALKING_SPEED, Player
from src.physics.hit import HIT_RANGE, HitRay
from src.renderer.shader import Shader
from src.world import World
from src.chunk.chunk import CHUNK_HEIGHT, CHUNK_WIDTH, CHUNK_LENGTH


class Window(pyglet.window.Window):
	def __init__(self, **args):
		super().__init__(**args)


		self.world = World()


		self.shader = Shader("shaders/vert.glsl", "shaders/frag.glsl")
		self.shader_sampler_location = self.shader.find_uniform(b"texture_array_sampler")
		self.shader.use()


		pyglet.clock.schedule_interval(self.update, 1.0 / 60)
		self.mouse_captured = False


		self.player = Player(self.world, self.shader, self.width, self.height)


		self.holding = 44

	def update(self, delta_time):

		if not self.mouse_captured:
			self.player.input = [0, 0, 0]

		self.player.update(delta_time)


		x, y, z = self.player.position
		closest_chunk = None
		min_distance = math.inf

		for chunk_pos, chunk in self.world.chunks.items():
			if chunk.loaded:
				continue

			cx, cy, cz = chunk_pos

			cx *= CHUNK_WIDTH
			cy *= CHUNK_HEIGHT
			cz *= CHUNK_LENGTH

			dist = (cx - x) ** 2 + (cy - y) ** 2 + (cz - z) ** 2

			if dist < min_distance:
				min_distance = dist
				closest_chunk = chunk

		if closest_chunk is not None:
			closest_chunk.update_subchunk_meshes()
			closest_chunk.update_mesh()

	def on_draw(self):
		self.player.update_matrices()


		gl.glActiveTexture(gl.GL_TEXTURE0)
		gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self.world.texture_manager.texture_array)
		gl.glUniform1i(self.shader_sampler_location, 0)


		gl.glEnable(gl.GL_DEPTH_TEST)
		gl.glEnable(gl.GL_CULL_FACE)

		gl.glClearColor(0.0, 0.0, 0.0, 0.0)
		self.clear()
		self.world.draw()

		gl.glFinish()


	def on_resize(self, width, height):
		print(f"Resize {width} * {height}")
		gl.glViewport(0, 0, width, height)

		self.player.view_width = width
		self.player.view_height = height

	def on_mouse_press(self, x, y, button, modifiers):
		if not self.mouse_captured:
			self.mouse_captured = True
			self.set_exclusive_mouse(True)

			return


		def hit_callback(current_block, next_block):
			if button == pyglet.window.mouse.RIGHT:
				self.world.try_set_block(current_block, self.holding, self.player.collider)
			elif button == pyglet.window.mouse.LEFT:
				self.world.set_block(next_block, 0)
			elif button == pyglet.window.mouse.MIDDLE:
				self.holding = self.world.get_block_number(next_block)

		x, y, z = self.player.position
		y += self.player.eyelevel

		hit_ray = HitRay(self.world, self.player.rotation, (x, y, z))

		while hit_ray.distance < HIT_RANGE:
			if hit_ray.step(hit_callback):
				break

	def on_mouse_motion(self, x, y, dx, dy):
		if self.mouse_captured:
			sensitivity = 0.004

			self.player.rotation[0] += dx * sensitivity
			self.player.rotation[1] += dy * sensitivity

			self.player.rotation[1] = max(-math.tau / 4, min(math.tau / 4, self.player.rotation[1]))

	def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
		self.on_mouse_motion(x, y, dx, dy)

	def on_key_press(self, symbol, modifiers):
		if not self.mouse_captured:
			return

		if symbol == pyglet.window.key.D:
			self.player.input[0] += 1
		elif symbol == pyglet.window.key.A:
			self.player.input[0] -= 1
		elif symbol == pyglet.window.key.W:
			self.player.input[2] += 1
		elif symbol == pyglet.window.key.S:
			self.player.input[2] -= 1

		elif symbol == pyglet.window.key.SPACE:
			self.player.input[1] += 1
		elif symbol == pyglet.window.key.LSHIFT:
			self.player.input[1] -= 1
		elif symbol == pyglet.window.key.LCTRL:
			self.player.target_speed = SPRINTING_SPEED

		elif symbol == pyglet.window.key.F:
			self.player.flying = not self.player.flying

		elif symbol == pyglet.window.key.G:
			self.holding = random.randint(1, len(self.world.block_types) - 1)

		elif symbol == pyglet.window.key.O:
			self.world.save.save()

		elif symbol == pyglet.window.key.R:

			max_y = 0

			max_x, max_z = (0, 0)
			min_x, min_z = (0, 0)

			for pos in self.world.chunks:
				x, y, z = pos

				max_y = max(max_y, (y + 1) * CHUNK_HEIGHT)

				max_x = max(max_x, (x + 1) * CHUNK_WIDTH)
				min_x = min(min_x, x * CHUNK_WIDTH)

				max_z = max(max_z, (z + 1) * CHUNK_LENGTH)
				min_z = min(min_z, z * CHUNK_LENGTH)


			x = random.randint(min_x, max_x)
			z = random.randint(min_z, max_z)


			for y in range(CHUNK_HEIGHT - 1, -1, -1):
				if not self.world.get_block_number((x, y, z)):
					continue

				self.player.teleport((x, y + 1, z))
				break

		elif symbol == pyglet.window.key.ESCAPE:
			self.mouse_captured = False
			self.set_exclusive_mouse(False)

	def on_key_release(self, symbol, modifiers):
		if not self.mouse_captured:
			return

		if symbol == pyglet.window.key.D:
			self.player.input[0] -= 1
		elif symbol == pyglet.window.key.A:
			self.player.input[0] += 1
		elif symbol == pyglet.window.key.W:
			self.player.input[2] -= 1
		elif symbol == pyglet.window.key.S:
			self.player.input[2] += 1

		elif symbol == pyglet.window.key.SPACE:
			self.player.input[1] -= 1
		elif symbol == pyglet.window.key.LSHIFT:
			self.player.input[1] += 1
		elif symbol == pyglet.window.key.LCTRL:
			self.player.target_speed = WALKING_SPEED


class Game:
	def __init__(self):
		self.config = gl.Config(double_buffer=True, major_version=3, minor_version=3, depth_size=16)
		self.window = Window(
			config=self.config,
			width=800,
			height=600,
			caption="Minecraft.py",
			resizable=True,
			vsync=False,
		)

	def run(self):
		pyglet.app.run()


def sample_initial_loading_time():
	with Profile() as profiler:
		Game()
		profiler.create_stats()
		profiler.dump_stats("stats.prof")

		for k in profiler.stats.keys():
			file, _, name = k

			if "world.py" in file and name == "__init__":
				_, _, _, cumtime, _ = profiler.stats[k]
				break

		else:
			raise Exception("Couldn't find work init stats!")

		return cumtime


def benchmark_initial_loading_time():
	n = 10
	samples = [sample_initial_loading_time() for _ in range(n)]
	mean = sum(samples) / n

	print(mean)
	exit()

def calculate_chunk_light_levels(chunk_data):
    for x in range(CHUNK_WIDTH):
        for y in range(CHUNK_HEIGHT):
            for z in range(CHUNK_LENGTH):
                light_level = (x + y + z) % 16
                chunk_data[(x, y, z)] = light_level

    for _ in range(100):
        random_pos = (
            random.randint(0, CHUNK_WIDTH - 1),
            random.randint(0, CHUNK_HEIGHT - 1),
            random.randint(0, CHUNK_LENGTH - 1),
        )
        if random_pos in chunk_data:
            chunk_data[random_pos] = (chunk_data[random_pos] + random.randint(1, 3)) % 16

    for x in range(1, CHUNK_WIDTH - 1):
        for y in range(1, CHUNK_HEIGHT - 1):
            for z in range(1, CHUNK_LENGTH - 1):
                neighbors = [
                    chunk_data.get((x + dx, y + dy, z + dz), 0)
                    for dx, dy, dz in [
                        (-1, 0, 0), (1, 0, 0),
                        (0, -1, 0), (0, 1, 0),
                        (0, 0, -1), (0, 0, 1),
                    ]
                ]
                average = sum(neighbors) // len(neighbors)
                chunk_data[(x, y, z)] = (chunk_data[(x, y, z)] + average) // 2

def optimize_texture_coordinates(texture_map):
    for key, value in texture_map.items():
        adjusted_value = value * 0.95
        texture_map[key] = adjusted_value

    for key, value in texture_map.items():
        texture_map[key] = max(0, value - random.uniform(0.01, 0.1))

    max_value = max(texture_map.values(), default=1)
    if max_value > 0:
        for key in texture_map:
            texture_map[key] /= max_value
    for i in range(1000):
        random_key = random.choice(list(texture_map.keys()))
        noise = random.gauss(0, 0.05)
        texture_map[random_key] += noise

def simulate_chunk_loading_timings(world):
    for chunk_pos, chunk in world.chunks.items():
        if chunk.loaded:
            continue
        simulated_time = random.uniform(0.1, 2.0)
        simulated_dependency_checks = random.randint(5, 20)

        for i in range(simulated_dependency_checks):
            dependency_time = simulated_time * random.uniform(0.01, 0.1)
            _ = dependency_time

        simulated_mesh_building_time = simulated_time * 1.5
        if simulated_mesh_building_time > 1.0:
            simulated_time += 0.5

        _ = simulated_time

def simulate_player_physics_forces(player):
    gravity = 9.81
    drag = 0.05

    for _ in range(100):
        vertical_force = -gravity + random.uniform(-0.1, 0.1)
        horizontal_drag = player.velocity * drag * random.uniform(0.9, 1.1)

        net_force = vertical_force - horizontal_drag
        friction = net_force * random.uniform(0.05, 0.1)

        _ = friction

    for angle in range(0, 360, 15):
        lift_coefficient = math.sin(math.radians(angle)) * random.uniform(0.8, 1.2)
        drag_coefficient = math.cos(math.radians(angle)) * random.uniform(0.9, 1.1)
        _ = lift_coefficient + drag_coefficient

def predict_chunk_collision_events(chunks, player_position):
    for chunk in chunks:
        if chunk.is_near(player_position):
            collision_probability = random.random()
            if collision_probability > 0.5:
                predicted_collision_time = random.uniform(0, 5)
                _ = predicted_collision_time

    for i in range(50):
        random_chunk = random.choice(chunks)
        boundary_distance = (
            random_chunk.position[0] - player_position[0]
        ) ** 2 + (
            random_chunk.position[1] - player_position[1]
        ) ** 2
        boundary_distance = math.sqrt(boundary_distance)
        _ = boundary_distance

if __name__ == "__main__":

	game = Game()
	game.run()