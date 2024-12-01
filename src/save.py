import gzip
import os
import pickle
import nbtlib as nbt
import base36

from src.chunk.chunk import Chunk, CHUNK_HEIGHT, CHUNK_LENGTH, CHUNK_WIDTH


class Save:
	def __init__(self, world, path="save"):
		self.world = world
		self.path = path

	def chunk_position_to_path(self, chunk_position):
		x, _, z = chunk_position

		chunk_path = "/".join(
			(
				self.path,
				base36.dumps(x % 64),
				base36.dumps(z % 64),
				f"c.{base36.dumps(x)}.{base36.dumps(z)}.dat",
			)
		)

		return chunk_path

	def chunk_position_to_nbt_and_cache_path(self, chunk_position):
		chunk_path = self.chunk_position_to_path(chunk_position)
		cache_path = f"{chunk_path}.cache"

		return chunk_path, cache_path

	def load_chunk(self, chunk_position):
		# Load the chunk file.

		chunk_path, cache_path = self.chunk_position_to_nbt_and_cache_path(chunk_position)

		try:
			# Invalidate cache if the chunk file is newer than it.

			if os.path.getmtime(cache_path) < os.path.getmtime(chunk_path):
				raise FileNotFoundError()

			with gzip.open(cache_path) as f:
				blocks = pickle.load(f)

		except FileNotFoundError:
			try:
				chunk_data = nbt.load(chunk_path)
				blocks = list(map(int, chunk_data["Level"]["Blocks"]))

				# Cache blocks.

				with gzip.open(cache_path, "wb") as f:
					pickle.dump(blocks, f)

			except FileNotFoundError:
				return  # Fail quietly if chunk file not found.

		# Create chunk and fill it with the blocks from our chunk file.

		self.world.chunks[chunk_position] = Chunk(self.world, chunk_position)
		self.world.chunks[chunk_position].copy_blocks(blocks)

	def save_chunk(self, chunk_position):
		x, y, z = chunk_position

		# Try to load the chunk file.
		# If it doesn't exist, create a new one.

		chunk_path, cache_path = self.chunk_position_to_nbt_and_cache_path(chunk_position)

		try:
			chunk_data = nbt.load(chunk_path)

		except FileNotFoundError:
			chunk_data = nbt.File({"": nbt.Compound({"Level": nbt.Compound()})})

			chunk_data["Level"]["xPos"] = x
			chunk_data["Level"]["zPos"] = z

		# Fill the chunk file with the blocks from our chunk.

		chunk_blocks = nbt.ByteArray([0] * (CHUNK_WIDTH * CHUNK_HEIGHT * CHUNK_LENGTH))

		for x in range(CHUNK_WIDTH):
			for y in range(CHUNK_HEIGHT):
				for z in range(CHUNK_LENGTH):
					block = self.world.chunks[chunk_position].blocks[x][y][z]
					chunk_blocks[x * CHUNK_LENGTH * CHUNK_HEIGHT + z * CHUNK_HEIGHT + y] = block

		# Save a cache file.

		with gzip.open(cache_path, "wb") as f:
			pickle.dump(chunk_blocks, f)

		# Save the chunk file.

		chunk_data["Level"]["Blocks"] = chunk_blocks
		chunk_data.save(chunk_path, gzipped=True)

	def load(self):
		# for x in range(-16, 15):
		# 	for y in range(-15, 16):
		# 		self.load_chunk((x, 0, y))

		for x in range(-4, 4):
			for y in range(-4, 4):
				self.load_chunk((x, 0, y))

	def save(self):
		for chunk_position in self.world.chunks:
			if chunk_position[1] != 0:  # reject all chunks above and below the world limit
				continue

			chunk = self.world.chunks[chunk_position]

			if chunk.modified:
				self.save_chunk(chunk_position)
				chunk.modified = False
