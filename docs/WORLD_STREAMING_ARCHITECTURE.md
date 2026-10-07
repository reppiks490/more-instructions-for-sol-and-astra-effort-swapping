# AEONFALL — World Streaming Architecture

AEONFALL is designed as one large streamed experience rather than a permanently loaded monolithic battlefield.

## World Partition
The project should enable World Partition streaming. Region geometry, ordinary AI, destructibles, loot actors, temporary VFX, and most encounter bodies should be spatially loaded. Only lightweight global state services stay permanently available.

## Regional Design
The macro-world is divided into 13 named regions. These are not menu-separated levels: they are authored geographic identities connected by traversable borders, special routes, vehicles, portals, and late-game shortcuts. The first production target is REG-001, The Ossuary March.

## HLOD and Skyline Language
Each region gets one or more recognizable distant silhouettes. Those silhouettes must have intentionally authored low LODs before HLOD generation so far-distance memory cost does not inherit full-resolution source assets.

## Massive Bosses
Skyscraper, regional, continent, and sky-scale bosses are presentation and orchestration problems, not single-mesh-size contests. Use:
- a lightweight authoritative encounter controller;
- streamed local weak-point or organ actors;
- local hazards and objectives;
- regional terrain or Scene Graph shells;
- distant HLOD/cinematic silhouettes;
- synchronized state replicated through the encounter contract.

This lets Orun, the Walking Continent, appear continent-sized while actual interactive gameplay remains partitionable and profileable.

## Profiling
Every region and major event must be tested with Spatial Profiler. Record actor count, Scene Graph entity count, object count, update time, and render cost during representative combat. Use Memory Snapshot on local PC sessions to locate high-cost loaded assets, then retest after optimization.

## Rule
No design earns the label “massive” by keeping massive amounts of content loaded at all times. Scale must survive streaming, cleanup, network replication, and the weakest supported target profile.
