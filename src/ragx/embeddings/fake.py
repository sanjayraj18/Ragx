import hashlib
import math
import random


def _embed(self, text: str) -> list[float]:
      seed = int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")
      rng = random.Random(seed)
      vector = [rng.gauss(0, 1) for _ in range(self._dimension)]
      norm = math.sqrt(sum(x * x for x in vector)) or 1.0
      return [x / norm for x in vector]