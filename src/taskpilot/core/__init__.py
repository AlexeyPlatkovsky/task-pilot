"""TaskPilot core domain layer.

Business rules live here. CLI and REST adapters call into this layer directly;
filesystem and index/cache details must not leak into the domain model.
"""
