#!/usr/bin/env python3
"""Build original, deterministic UEFN starter geometry without external packages.

Source coordinates are X east, Y north, Z up, in meters. GLB is converted to
glTF's right-handed, Y-up meter coordinates; OBJ and placement transforms use
Unreal centimeter coordinates. This is source geometry, not a UEFN project.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "assets/source/ossuary_starter"
MATERIALS = [
    ("GraveBasalt", (0.15, 0.18, 0.21, 1), 0.05, 0.92, None),
    ("OssuaryLimestone", (0.53, 0.50, 0.43, 1), 0.0, 0.95, None),
    ("BlackIron", (0.07, 0.09, 0.11, 1), 0.65, 0.58, None),
    ("LedgerCopper", (0.48, 0.25, 0.12, 1), 0.6, 0.7, None),
    ("TreasuryJade", (0.13, 0.62, 0.42, 1), 0.0, 0.55, (0.05, 0.35, 0.18)),
    ("DecreeCrimson", (0.53, 0.07, 0.10, 1), 0.0, 0.78, None),
    ("PilgrimAmber", (0.83, 0.54, 0.16, 1), 0.0, 0.4, (0.45, 0.22, 0.04)),
]


def subtract(a, b):
    return tuple(x - y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def gltf_vector(p):
    return (p[0], p[2], -p[1])


class Mesh:
    """Collection of closed convex solids, with per-face normals and UVs."""
    def __init__(self, name, purpose):
        self.name, self.purpose = name, purpose
        self.positions, self.normals, self.uvs = [], [], []
        self.material_indices = {}
        self.solids = []

    def solid(self, points, faces, material=0, label="solid"):
        center = tuple(sum(p[i] for p in points)/len(points) for i in range(3))
        first_vertex = len(self.positions)
        all_triangles = []
        for face in faces:
            face = list(face)
            normal = cross(subtract(points[face[1]], points[face[0]]),
                           subtract(points[face[2]], points[face[0]]))
            face_center = tuple(sum(points[v][i] for v in face)/len(face) for i in range(3))
            if dot(normal, subtract(face_center, center)) < 0:
                face.reverse()
                normal = tuple(-v for v in normal)
            length = math.sqrt(dot(normal, normal))
            if length < 1e-10:
                raise ValueError(f"{self.name}/{label}: zero-area face")
            normal = tuple(v/length for v in normal)
            base = len(self.positions)
            for vertex in face:
                p = points[vertex]
                self.positions.append(p)
                self.normals.append(normal)
                # Planar repeatable UVs at one meter per tile; dominant projection.
                dominant = max(range(3), key=lambda i: abs(normal[i]))
                axes = [i for i in range(3) if i != dominant]
                self.uvs.append((p[axes[0]], p[axes[1]]))
            for i in range(1, len(face)-1):
                triangle = (base, base+i, base+i+1)
                self.material_indices.setdefault(material, []).extend(triangle)
                all_triangles.append(triangle)
        self.solids.append({"label": label, "vertices_m": [list(p) for p in points],
                            "vertices_cm": [[round(v*100, 6) for v in p] for p in points],
                            "triangles": all_triangles, "first_vertex": first_vertex})

    def box(self, center, size, material=0, label="box", yaw=0):
        angle = math.radians(yaw)
        c, s = math.cos(angle), math.sin(angle)
        points = []
        for x, y, z in ((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
                        (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)):
            x, y, z = x*size[0]/2, y*size[1]/2, z*size[2]/2
            points.append((center[0]+x*c-y*s, center[1]+x*s+y*c, center[2]+z))
        self.solid(points, ((0,3,2,1),(4,5,6,7),(0,1,5,4),
                           (1,2,6,5),(2,3,7,6),(3,0,4,7)), material, label)

    def prism(self, polygon, z0, z1, material=0, label="prism"):
        n = len(polygon)
        points = [(x,y,z) for z in (z0,z1) for x,y in polygon]
        faces = [tuple(range(n-1,-1,-1)), tuple(range(n,2*n))]
        faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        self.solid(points, faces, material, label)

    def taper(self, center_xy, radius0, radius1, z0, z1, material=0, label="octagon", sides=8):
        points = [(center_xy[0]+radius*math.cos(math.tau*i/sides+math.pi/8),
                   center_xy[1]+radius*math.sin(math.tau*i/sides+math.pi/8),z)
                  for radius,z in ((radius0,z0),(radius1,z1)) for i in range(sides)]
        faces = [tuple(range(sides-1,-1,-1)), tuple(range(sides,2*sides))]
        faces += [(i,(i+1)%sides,(i+1)%sides+sides,i+sides) for i in range(sides)]
        self.solid(points, faces, material, label)

    def xz_extrusion(self, polygon, depth, material=0, label="xz_prism"):
        n = len(polygon)
        points = [(x,y,z) for y in (-depth/2, depth/2) for x,z in polygon]
        faces = [tuple(range(n)), tuple(range(n,2*n))]
        faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        self.solid(points, faces, material, label)

    def bounds(self):
        return {"min": [min(p[i] for p in self.positions) for i in range(3)],
                "max": [max(p[i] for p in self.positions) for i in range(3)]}

    def metadata(self):
        return {"id": self.name, "purpose": self.purpose,
                "files": {ext: f"meshes/{self.name}.{ext}" for ext in ("glb","obj","mtl")},
                "bounds_m": self.bounds(), "vertices": len(self.positions),
                "triangles": sum(len(i)//3 for i in self.material_indices.values()),
                "collision": {"strategy": "convex_components", "hulls": [
                    {key: solid[key] for key in ("label","vertices_m","vertices_cm")}
                    for solid in self.solids]},
                "uv_policy": "planar, one source meter per UV repeat; no texture dependencies"}


def build_modules():
    modules = []
    def mesh(name, purpose):
        item = Mesh("SM_AEON_"+name, purpose)
        modules.append(item)
        return item
    for width in (4,8):
        m = mesh(f"Floor_{width}m", "Level walkable slab; origin on upper surface.")
        m.box((0,0,-0.15), (width,width,0.3), 0, "floor_slab")
    m = mesh("Wall_4m", "Six-meter crypt wall; align center to room perimeter.")
    m.box((0,0,3), (4,0.6,6), 0, "wall_body")
    m.box((0,0,0.25), (4.1,0.85,0.5), 1, "plinth")
    m.box((0,0,6.1), (4.2,0.95,0.4), 1, "coping")
    m.box((0,-0.33,3), (0.15,0.10,4.5), 3, "ledger_seam")
    m = mesh("PointedArch_8m", "Open portal: 5m clear width at floor, 6m central height.")
    inner = [(-2.5,0),(-2.5,3),(-2.3,4),(-1.5,5),(0,6),(1.5,5),(2.3,4),(2.5,3),(2.5,0)]
    outer = [(-4,0),(-4,3.2),(-3.8,4.8),(-2.7,6.4),(0,7.5),(2.7,6.4),(3.8,4.8),(4,3.2),(4,0)]
    for i in range(len(inner)-1):
        m.xz_extrusion((inner[i],outer[i],outer[i+1],inner[i+1]), 1, 1, f"voussoir_{i}")
    m.box((0,0,7.65), (0.35,1.2,0.65), 3, "keystone")
    m = mesh("RibColumn_6m", "Octagonal support with copper cap; edge placement avoids navigation lanes.")
    m.taper((0,0), 0.9,0.9,0,0.4,1,"base")
    m.taper((0,0), 0.52,0.42,0.4,5.3,1,"shaft")
    m.taper((0,0), 0.42,0.8,5.3,5.7,3,"capital")
    m.taper((0,0), 0.8,0.8,5.7,6,1,"abacus")
    m = mesh("Buttress_7m", "Triangular exterior rib; keep outside room perimeter.")
    m.box((0,0.4,0.3), (1.7,3,0.6), 1,"foot")
    m.xz_extrusion(((-0.65,0.6),(0.65,0.6),(0.65,6.5),(-0.65,7)),1,1,"vertical_rib")
    # A genuine wedge extending outward along local Y.
    m.solid([(-0.6,0,0.6),(0.6,0,0.6),(-0.6,1.8,0.6),(0.6,1.8,0.6),
             (-0.6,0,6),(0.6,0,6)], ((0,2,3,1),(0,1,5,4),(0,4,2),(1,3,5),(2,4,5,3)), 0,"flying_rib")
    m = mesh("Stairs_4m_Rise1m", "Eight 12.5cm steps; climb toward local +Y.")
    for i in range(8):
        h = (i+1)*0.125
        m.box((0,-2+(i+0.5)*0.5,h/2),(4,0.5,h),1,f"step_{i+1}")
    m = mesh("Ramp_4m_Rise1m", "14 degree accessible alternative; rises toward local +Y.")
    m.solid([(-2,-2,0),(2,-2,0),(-2,2,0),(2,2,0),(-2,2,1),(2,2,1)],
            ((0,2,3,1),(0,1,5,4),(0,4,2),(1,3,5),(2,4,5,3)),0,"ramp")
    m = mesh("TreasuryAnchor", "Static stand-in for BOS-011 treasury objective; no gameplay behavior.")
    m.taper((0,0),1.4,1.4,0,0.35,1,"pedestal")
    m.taper((0,0),0.7,0.5,0.35,1.7,2,"ledger_column")
    m.taper((0,0),0.48,0.12,1.7,2.7,4,"jade_core")
    for i in range(4):
        a = i*math.pi/2
        m.box((0.8*math.cos(a),0.8*math.sin(a),1.55),(.22,.22,2.4),3,f"crown_prong_{i}")
    m = mesh("BlackThrone", "Original ribbed sovereign throne; forward direction is local -Y.")
    m.box((0,0,0.2),(6,5,0.4),0,"plinth")
    m.box((0,0.25,0.7),(3.2,2.7,0.6),1,"lower_step")
    m.box((0,0.25,1.2),(2.7,2.3,0.4),2,"seat_base")
    m.box((0,0.25,1.55),(2.4,2.1,0.3),3,"seat")
    m.box((0,1.1,3.1),(2.5,0.5,3),2,"back")
    for x in (-1.45,1.45):
        m.box((x,0,1.65),(.45,2.8,0.4),1,"arm")
        m.box((x,-1.0,1.1),(.4,.4,1.4),2,"arm_support")
    for i,x in enumerate((-2.4,-1.6,-.8,0,.8,1.6,2.4)):
        top = 6.8-abs(x)*.6
        # Faceted bone-fin silhouette, closed convex geometry.
        m.xz_extrusion(((x-.13,2),(x+.13,2),(x+.08,top),(x,top+.5),(x-.08,top)), .35, 1,f"crown_rib_{i}")
    m.box((0,0.805,3.25),(0.7,.15,1.2),4,"throne_ledger")
    m = mesh("MarketStall_6m", "Open sided quartermaster/event stall; 3.2m under canopy clearance.")
    for x in (-2.7,2.7):
        for y in (-1.6,1.6):
            m.box((x,y,1.6),(.25,.25,3.2),2,"stall_post")
    m.xz_extrusion(((-3,3.2),(0,4),(0,4.2),(-3,3.4)),4,0,"canopy_left")
    m.xz_extrusion(((0,4),(3,3.2),(3,3.4),(0,4.2)),4,0,"canopy_right")
    m.box((0,1.2,.65),(4.6,1,1.3),1,"counter")
    m.box((0,-1.9,3),(2.2,.15,.55),3,"sign_board")
    m = mesh("Sarcophagus", "Faceted six-sided corpse-economy lot prop, original silhouette.")
    coffin = [(-.6,-1.7),(.6,-1.7),(1,-.9),(.85,1.5),(-.85,1.5),(-1,-.9)]
    m.prism(coffin,0,.95,1,"coffin")
    m.prism([(x*1.05,y*1.02) for x,y in coffin],.95,1.15,0,"lid")
    m.box((0,-.2,1.22),(.18,1.8,.14),3,"ledger_spine")
    m = mesh("GraveObelisk", "Angular pilgrimage marker with inset ledger seam.")
    m.box((0,0,.15),(1.4,1.4,.3),1,"foot")
    m.taper((0,0),.52,.36,.3,2.7,0,"shaft",4)
    m.taper((0,0),.36,.02,2.7,3.5,1,"pinnacle",4)
    m.box((0,-.33,1.5),(.1,.08,1.6),3,"inset")
    m = mesh("PilgrimLantern", "Static emissive lantern geometry; lighting must be authored in editor.")
    m.taper((0,0),.55,.55,0,.25,1,"foot")
    m.taper((0,0),.15,.15,.25,2.4,2,"stem")
    m.taper((0,0),.48,.48,2.4,2.6,3,"bowl")
    m.taper((0,0),.3,.2,2.6,3.2,6,"amber")
    m.taper((0,0),.5,.1,3.2,3.6,2,"hood")
    m = mesh("GateSpire_14m", "Stepped skyline marker for Ossuary March; solid, exterior-only.")
    m.box((0,0,.4),(4,4,.8),1,"foundation")
    m.box((0,0,3.8),(2.8,2.8,6),0,"tower")
    m.box((0,0,7),(3.3,3.3,.5),1,"belt")
    m.taper((0,0),1.55,.75,7.25,11,0,"upper",4)
    m.taper((0,0),.9,.06,11,14,1,"spire",4)
    m = mesh("Causeway_8m", "8m long by 4m wide deck, 3.2m clearance between parapets.")
    m.box((0,0,-.3),(8,4,.6),0,"deck")
    for y in (-1.8,1.8):
        m.box((0,y,.55),(8,.4,1.1),1,"parapet")
    m = mesh("CheckpointPlinth", "Visual checkpoint locator; wire actual devices separately.")
    m.box((0,0,.1),(2,2,.2),1,"pad")
    for x in (-.9,.9):
        m.box((x,0,.23),(.1,1.8,.06),4,"inlay")
    m = mesh("BasisMarker", "Scale/axis calibration: X crimson, Y jade, Z limestone, 2m each.")
    m.box((1,0,.05),(2,.1,.1),5,"axis_X_2m")
    m.box((0,1,.05),(.1,2,.1),4,"axis_Y_2m")
    m.box((0,0,1),(.1,.1,2),1,"axis_Z_2m")
    return modules


ROOMS = [
    {"id":"outer_market","label":"Outer Market / faction choice","center_m":[0,0],"size_m":[32,28],"act":1},
    {"id":"disruption_chambers","label":"Corpse-economy disruption","center_m":[0,38],"size_m":[24,24],"act":2},
    {"id":"construction_gauntlet","label":"Necromancer construction gauntlet","center_m":[0,80],"size_m":[20,36],"act":3},
    {"id":"miniboss_branch","label":"Red Mason branch / BOS-005","center_m":[-34,94],"size_m":[24,24],"act":4},
    {"id":"throne_approach","label":"King Without Pulse approach","center_m":[0,116],"size_m":[16,16],"act":5},
    {"id":"black_throne","label":"Black Throne / BOS-011","center_m":[0,150],"size_m":[44,44],"act":5},
]


def build_layout():
    placements, markers = [], []
    counter = 0
    def place(mesh, p, yaw=0, zone="march", role="architecture", scale=(1,1,1)):
        nonlocal counter
        counter += 1
        placements.append({"name":f"AEON_{zone}_{counter:04d}","mesh":"SM_AEON_"+mesh,
                           "location_cm":[round(v*100,5) for v in p],
                           "rotation_deg":[0,yaw,0],"scale":list(scale),"zone":zone,"role":role})
    def floor_rect(x,y,w,h,zone):
        for xi in range(int(w/4)):
            for yi in range(int(h/4)):
                place("Floor_4m",(x-w/2+2+xi*4,y-h/2+2+yi*4,0),zone=zone)
    for room in ROOMS:
        zone=room["id"]
        x,y=room["center_m"]
        w,h=room["size_m"]
        floor_rect(x,y,w,h,zone)
        for side in (-1,1):
            # Partial 2m panels keep an exact 8m portal opening in 20/44m rooms.
            # Skipping panels by center alone would leave only a 4m gap there.
            has_door = zone != "miniboss_branch" and (zone != "black_throne" or side == -1)
            spans=((-w/2,-4),(4,w/2)) if has_door else ((-w/2,w/2),)
            for lo,hi in spans:
                cursor=lo
                while cursor<hi-1e-6:
                    width=min(4,hi-cursor)
                    place("Wall_4m",(x+cursor+width/2,y+side*h/2,0),zone=zone,scale=(width/4,1,1))
                    cursor+=width
            if zone != "miniboss_branch" and (zone != "black_throne" or side == -1):
                place("PointedArch_8m",(x,y+side*h/2,0),zone=zone)
            for i in range(int(h/4)):
                yc=y-h/2+2+i*4
                branch_door = (zone == "construction_gauntlet" and side == -1 and yc >= 90)
                branch_door |= (zone == "miniboss_branch" and side == 1 and abs(yc-94)<4)
                if branch_door:
                    continue
                place("Wall_4m",(x+side*w/2,yc,0),90,zone=zone)
        for sx in (-1,1):
            for sy in (-1,1):
                if zone == "construction_gauntlet" and sx == -1 and sy == 1:
                    # The northwest corner is the branch portal; its pier replaces the column.
                    continue
                place("RibColumn_6m",(x+sx*(w/2-.8),y+sy*(h/2-.8),0),zone=zone)
        # Exterior buttresses provide a gothic silhouette without shrinking clear lanes.
        for sx in (-1,1):
            for offset in (-h/4,h/4):
                place("Buttress_7m",(x+sx*(w/2+1),y+offset,0),-90*sx,zone=zone)
    # Flat connectors never require jumping; arch mouths are eight meters overall.
    for y,h,zone in ((20,12,"market_link"),(56,12,"crypt_link"),(103,10,"gauntlet_link"),(126,4,"throne_link")):
        # 10m link uses three 4m rows, overlapping the room edges by 1m.
        floor_rect(0,y,8,math.ceil(h/4)*4,zone)
    floor_rect(-16,94,12,8,"branch_link")
    for x in (-22,-10):
        place("PointedArch_8m",(x,94,0),90,zone="branch_link")
    # A small marsh approach, kept flat and joined to the market's south mouth.
    floor_rect(0,-24,8,20,"graveglass_causeway")
    for y in (-26,-18):
        for x in (-7,7):
            place("PilgrimLantern",(x,y,0),zone="graveglass_causeway",role="decoration")
    for x in (-18,18):
        place("GateSpire_14m",(x,-15,0),zone="outer_market",role="skyline")
    for x in (-10,10):
        for y in (-7,7):
            place("MarketStall_6m",(x,y,0),90 if x<0 else -90,zone="outer_market",role="prop")
    for x in (-7,7):
        for y in (33,43):
            place("Sarcophagus",(x,y,0),90,zone="disruption_chambers",role="prop")
    for x in (-7,7):
        for y in (68,80,90):
            place("RibColumn_6m",(x,y,0),zone="construction_gauntlet",role="cover")
    for x,y in ((-40,88),(-28,100)):
        place("TreasuryAnchor",(x,y,0),zone="miniboss_branch",role="objective_proxy")
    for x in (-15,15):
        for y in (138,150,164):
            place("RibColumn_6m",(x,y,0),zone="black_throne",role="cover")
    for suffix,x in (("A",-12),("B",12)):
        place("TreasuryAnchor",(x,154,0),zone="black_throne",role="objective_proxy")
        markers.append({"id":"OBJ-BOS011-BREAK-TREASURY-"+suffix,"kind":"objective", "location_cm":[x*100,15400,120],"radius_cm":140})
    place("BlackThrone",(0,165,0),zone="black_throne",role="boss_proxy")
    for x,y in ((-7,-30),(7,-30),(-20,10),(20,10),(-18,115),(18,115)):
        place("GraveObelisk",(x,y,0),zone="march",role="decoration")
    for i,(x,y) in enumerate(((0,-10),(0,29),(0,65),(0,119)),1):
        place("CheckpointPlinth",(x+5,y,0),zone="checkpoint",role="device_proxy")
        markers.append({"id":f"CHECKPOINT-{i}","kind":"checkpoint","location_cm":[x*100,y*100,100],"radius_cm":250})
    markers += [
        {"id":"PLAYER-SPAWN","kind":"player_spawn","location_cm":[0,-2900,100],"radius_cm":200},
        {"id":"EC_BOS_005","kind":"boss","location_cm":[-3400,9400,100],"radius_cm":900},
        {"id":"EC_BOS_011","kind":"boss","location_cm":[0,15000,100],"radius_cm":2000},
        {"id":"SG-BOS011-TAX-COLLECTORS","kind":"spawn_group","location_cm":[-1600,14000,100],"radius_cm":250},
        {"id":"SG-BOS011-BOUGHT-MINIONS","kind":"spawn_group","location_cm":[1600,14000,100],"radius_cm":250},
        {"id":"EVT-011-MARKET","kind":"world_event","location_cm":[0,0,100],"radius_cm":1200},
        {"id":"GRAVE-MARKET-QUARTERMASTER","kind":"shop","location_cm":[-1000,-700,100],"radius_cm":200},
    ]
    place("BasisMarker",(-25,-25,0),zone="calibration",role="calibration")
    paths = [
        {"id":"main_route","points_cm":[[0,-2900,0],[0,0,0],[0,3800,0],[0,8000,0],[0,11600,0],[0,15000,0]],
         "required_clear_width_cm":480,"required_clear_height_cm":300},
        {"id":"miniboss_branch","points_cm":[[0,9400,0],[-3400,9400,0]],
         "required_clear_width_cm":480,"required_clear_height_cm":300},
    ]
    return placements, markers, paths


def check_geometry(meshes):
    """Check each closed solid, independent of intentionally touching solids."""
    for mesh in meshes:
        for p in mesh.positions+mesh.normals:
            if not all(math.isfinite(v) for v in p):
                raise ValueError(mesh.name+": nonfinite vertex or normal")
        for solid in mesh.solids:
            edges, volume = {}, 0.0
            for tri in solid["triangles"]:
                if len(set(tri)) != 3 or not all(0<=i<len(mesh.positions) for i in tri):
                    raise ValueError(mesh.name+": invalid triangle indices")
                ps = [mesh.positions[i] for i in tri]
                n = cross(subtract(ps[1],ps[0]),subtract(ps[2],ps[0]))
                if dot(n,n)<1e-18:
                    raise ValueError(mesh.name+": degenerate triangle")
                volume += dot(ps[0],cross(ps[1],ps[2]))/6
                for a,b in zip(ps,ps[1:]+ps[:1]):
                    a,b = tuple(round(v,8) for v in a),tuple(round(v,8) for v in b)
                    edge = tuple(sorted((a,b)))
                    count,balance = edges.get(edge,(0,0))
                    edges[edge]=(count+1,balance+(1 if a<b else -1))
            if not all(count==2 and balance==0 for count,balance in edges.values()):
                raise ValueError(f"{mesh.name}/{solid['label']}: nonmanifold or inconsistent winding")
            if volume <= 1e-8:
                raise ValueError(f"{mesh.name}/{solid['label']}: nonpositive volume {volume}")


def material_json():
    result = []
    for name,rgba,metal,rough,emission in MATERIALS:
        m = {"name":name,"pbrMetallicRoughness":{"baseColorFactor":rgba,"metallicFactor":metal,"roughnessFactor":rough}}
        if emission:
            m["emissiveFactor"] = emission
        result.append(m)
    return result


def encode_glb(meshes, placements=None):
    binary = bytearray()
    doc = {"asset":{"version":"2.0","generator":"AEONFALL original deterministic geometry generator v1"},
           "scene":0,"scenes":[{"name":"The Ossuary Exchange","nodes":[]}],"nodes":[],"meshes":[],
           "materials":material_json(),"accessors":[],"bufferViews":[],"buffers":[]}
    def accessor(values,fmt,component,kind,target):
        while len(binary)%4:
            binary.append(0)
        offset = len(binary)
        values = list(values)
        flat = [v for row in values for v in row] if kind != "SCALAR" else values
        binary.extend(struct.pack("<"+str(len(flat))+fmt,*flat))
        view = len(doc["bufferViews"])
        doc["bufferViews"].append({"buffer":0,"byteOffset":offset,"byteLength":len(binary)-offset,"target":target})
        item = {"bufferView":view,"byteOffset":0,"componentType":component,"count":len(values),"type":kind}
        if kind == "VEC3" and target == 34962:
            item.update(min=[min(p[i] for p in values) for i in range(3)],max=[max(p[i] for p in values) for i in range(3)])
        index = len(doc["accessors"])
        doc["accessors"].append(item)
        return index
    for mesh in meshes:
        pos=accessor((gltf_vector(v) for v in mesh.positions),"f",5126,"VEC3",34962)
        nor=accessor((gltf_vector(v) for v in mesh.normals),"f",5126,"VEC3",34962)
        uv=accessor(mesh.uvs,"f",5126,"VEC2",34962)
        primitives=[]
        for material,indices in sorted(mesh.material_indices.items()):
            idx=accessor(indices,"I",5125,"SCALAR",34963)
            primitives.append({"attributes":{"POSITION":pos,"NORMAL":nor,"TEXCOORD_0":uv},"indices":idx,"material":material,"mode":4})
        doc["meshes"].append({"name":mesh.name,"primitives":primitives})
    if placements is None:
        doc["nodes"].append({"name":meshes[0].name,"mesh":0})
    else:
        mesh_index={mesh.name:i for i,mesh in enumerate(meshes)}
        for p in placements:
            theta=math.radians(p["rotation_deg"][1])/2
            doc["nodes"].append({"name":p["name"],"mesh":mesh_index[p["mesh"]],
                                 "translation":gltf_vector([v/100 for v in p["location_cm"]]),
                                 "rotation":[0,math.sin(theta),0,math.cos(theta)],"scale":p["scale"],
                                 "extras":{"zone":p["zone"],"role":p["role"]}})
    doc["scenes"][0]["nodes"]=list(range(len(doc["nodes"])))
    doc["buffers"]=[{"byteLength":len(binary)}]
    payload=json.dumps(doc,separators=(",",":"),ensure_ascii=False).encode()
    payload += b" "*((-len(payload))%4)
    binary += b"\0"*((-len(binary))%4)
    length=12+8+len(payload)+8+len(binary)
    return (struct.pack("<III",0x46546C67,2,length)+struct.pack("<II",len(payload),0x4E4F534A)+payload+
            struct.pack("<II",len(binary),0x004E4942)+binary)


def write_obj(mesh,path):
    lines=["# AEONFALL original source. Coordinates: centimeters, X east / Y north / Z up.",
           "# GLB alternative uses glTF meter units. Do not multiply this OBJ by 100.",
           f"mtllib {mesh.name}.mtl",f"o {mesh.name}"]
    lines += ["v "+" ".join(f"{v*100:.6f}" for v in p) for p in mesh.positions]
    lines += ["vt "+" ".join(f"{v:.6f}" for v in p) for p in mesh.uvs]
    lines += ["vn "+" ".join(f"{v:.7f}" for v in p) for p in mesh.normals]
    lines.append("s off")
    for material,indices in sorted(mesh.material_indices.items()):
        lines.append("usemtl "+MATERIALS[material][0])
        for i in range(0,len(indices),3):
            lines.append("f "+" ".join(f"{v+1}/{v+1}/{v+1}" for v in indices[i:i+3]))
    path.write_text("\n".join(lines)+"\n",encoding="utf-8")
    mtl=[]
    for name,rgba,metal,rough,emission in MATERIALS:
        mtl += [f"newmtl {name}","Kd "+" ".join(str(v) for v in rgba[:3]),"Ka 0 0 0","d 1", "illum 2",f"Ns {round((1-rough)*80)}"]
        if emission:
            mtl.append("Ke "+" ".join(str(v) for v in emission))
        mtl.append("")
    path.with_suffix(".mtl").write_text("\n".join(mtl),encoding="utf-8")


def distance_to_rect(x,y,cx,cy,w,h):
    return math.hypot(max(abs(x-cx)-w/2,0),max(abs(y-cy)-h/2,0))


def write_heightmap(output):
    # 253 = 4 components x 63 quads + 1, a standard Unreal Landscape resolution.
    resolution,spacing,z_scale = 253,2,20
    origin=(-252,-152)
    flat_rects=[(*r["center_m"],*r["size_m"]) for r in ROOMS]
    flat_rects += [(0,-10,12,55),(0,20,12,12),(0,56,12,12),(0,104,12,16),(0,126,12,8),(-16,94,12,12)]
    values=[]
    for yi in range(resolution):
        y=origin[1]+yi*spacing
        for xi in range(resolution):
            x=origin[0]+xi*spacing
            h=(2.2*math.sin(x*.025+y*.012)+1.5*math.sin(y*.042-x*.009)+
               10*math.exp(-((x+125)**2+(y-95)**2)/9500)+
               8*math.exp(-((x-155)**2+(y-200)**2)/12000)-
               4*math.exp(-((x-55)**2+(y+45)**2)/2400))
            d=min(distance_to_rect(x,y,*r) for r in flat_rects)
            # Keep terrain below slabs/thresholds, then blend to marsh/ridge shapes.
            t=max(0,min(1,(d-4)/20))
            smooth=t*t*(3-2*t)
            h=-.32*(1-smooth)+h*smooth
            values.append(round(32768+h*100*128/z_scale))
    if not all(0<=v<=65535 for v in values):
        raise ValueError("heightmap samples clipped")
    raw=struct.pack("<"+str(len(values))+"H",*values)
    (output/"landscape/ossuary_march_253.r16").write_bytes(raw)
    # PNG requires network byte order and grayscale color type 0, bit depth 16.
    rows=b"".join(b"\0"+struct.pack(">"+str(resolution)+"H",*values[y*resolution:(y+1)*resolution]) for y in range(resolution))
    def chunk(kind,data):
        return struct.pack(">I",len(data))+kind+data+struct.pack(">I",zlib.crc32(kind+data)&0xFFFFFFFF)
    png=b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",resolution,resolution,16,0,0,0,0))+chunk(b"IDAT",zlib.compress(rows,9))+chunk(b"IEND",b"")
    (output/"landscape/ossuary_march_253.png").write_bytes(png)
    return {"r16":"landscape/ossuary_march_253.r16","png":"landscape/ossuary_march_253.png",
            "resolution":[resolution,resolution],"r16_format":"unsigned 16-bit little-endian, row-major, no header",
            "png_format":"16-bit grayscale","sample_spacing_cm":200,"landscape_scale":[200,200,z_scale],
            "height_encoding":"height_cm = (sample - 32768) * Z_scale / 128",
            "landscape_actor_location_cm":[0,10000,0],"southwest_sample_cm":[-25200,-15200,0],
            "extent_cm":[50400,50400],"recommended_sections_per_component":1,"recommended_quads_per_section":63,
            "recommended_component_grid":[4,4],"min_height_m":(min(values)-32768)*z_scale/128/100,
            "max_height_m":(max(values)-32768)*z_scale/128/100,
            "notes":["Dungeon footprint and approach are flattened at -32cm; slab upper faces are at 0cm.",
                     "Landscape is optional. Verify first/last sample orientation against the layout before accepting import.",
                     "Landscape actor location assumes the editor centers the 253-square grid; if imported at a corner, use southwest_sample_cm."]}


def write_map(output,placements,paths):
    # Accessible vector plan; source geometry remains the GLB/OBJ, not this drawing.
    scale=4
    def xy(x,y): return (260+x*scale,840-y*scale)
    lines=['<svg xmlns="http://www.w3.org/2000/svg" width="660" height="1040" viewBox="0 0 660 1040" role="img" aria-label="Ossuary Exchange starter plan in meters">',
           '<rect width="660" height="1040" fill="#101820"/>',
           '<style>text{font-family:system-ui,sans-serif;fill:#e8e3d9;font-size:12px}.label{font-size:14px;font-weight:600}.small{font-size:10px}</style>',
           '<text x="24" y="30" font-size="24">AEONFALL · The Ossuary Exchange</text>',
           '<text x="24" y="53">Original importable greybox · plan in meters · north ↑</text>']
    for p in paths:
        points=" ".join(f"{xy(a/100,b/100)[0]},{xy(a/100,b/100)[1]}" for a,b,_ in p["points_cm"])
        lines.append(f'<polyline points="{points}" stroke="#244236" stroke-width="32" fill="none"/>')
    for room in ROOMS:
        x,y=room["center_m"];w,h=room["size_m"]
        px,py=xy(x-w/2,y+h/2)
        lines.append(f'<rect x="{px}" y="{py}" width="{w*scale}" height="{h*scale}" fill="#27313b" stroke="#b2a58f" stroke-width="3"/>')
        lx,ly=xy(x,y)
        lines.append(f'<text class="small" x="{lx}" y="{ly+4}" text-anchor="middle">{w} × {h}m</text>')
        lines.append(f'<text class="label" x="{px+w*scale+14}" y="{py+12}">{room["label"].replace(" / "," · ")}</text>')
    for p in placements:
        if p["role"] in ("objective_proxy","boss_proxy","cover","prop"):
            x,y,_=p["location_cm"];px,py=xy(x/100,y/100)
            color={"objective_proxy":"#6dd3a0","boss_proxy":"#b98756","cover":"#aaa08c","prop":"#826950"}[p["role"]]
            lines.append(f'<circle cx="{px}" cy="{py}" r="4" fill="{color}"/>')
    for p in paths:
        points=" ".join(f"{xy(a/100,b/100)[0]},{xy(a/100,b/100)[1]}" for a,b,_ in p["points_cm"])
        lines.append(f'<polyline points="{points}" stroke="#87cbaa" stroke-width="2" stroke-dasharray="5 4" fill="none"/>')
    lines += ['<text x="24" y="965">Portals: 5m clear width at floor · routes tested for 4.8m × 3m envelope</text>',
              '<text x="24" y="987">Green: treasury anchors · copper: throne · gray: cover · brown: market/crypt props</text>',
              '<path d="M24 1010h160m-160-4v8m160-8v8" stroke="#e8e3d9"/>',
              '<text x="190" y="1014">40m</text>','</svg>']
    (output/"layout_plan.svg").write_text("\n".join(lines)+"\n",encoding="utf-8")


def generate(output):
    for folder in (output,output/"meshes",output/"landscape"):
        folder.mkdir(parents=True,exist_ok=True)
    modules=build_modules()
    check_geometry(modules)
    placements,markers,paths=build_layout()
    for mesh in modules:
        (output/f"meshes/{mesh.name}.glb").write_bytes(encode_glb([mesh]))
        write_obj(mesh,output/f"meshes/{mesh.name}.obj")
    (output/"ossuary_exchange_preview.glb").write_bytes(encode_glb(modules,placements))
    gallery=[{"name":m.name,"mesh":m.name,"location_cm":[(i%4)*1400,(i//4)*2200,0],
              "rotation_deg":[0,0,0],"scale":[1,1,1],"zone":"module_gallery","role":"preview"}
             for i,m in enumerate(modules)]
    (output/"ossuary_module_gallery.glb").write_bytes(encode_glb(modules,gallery))
    landscape=write_heightmap(output)
    write_map(output,placements,paths)
    files=[]
    for path in sorted(output.rglob("*")):
        if path.is_file() and (path.suffix in (".glb",".obj",".mtl",".r16",".png",".svg")):
            data=path.read_bytes()
            files.append({"path":path.relative_to(output).as_posix(),"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()})
    manifest={"schema_version":1,"pack_id":"AEONFALL-OSSUARY-STARTER-001","status":"source_assets_editor_validation_pending",
              "provenance":{"original":True,"generator":"tools/build_ossuary_starter_assets.py","external_geometry":False,
                            "authored_for":"AEONFALL; inspired by its original Ossuary March and encounter specifications"},
              "source_specs":["content/vertical_slice/slice_001_ossuary_march.json","content/vertical_slice/slice_001_encounters.json"],
              "coordinates":{"source":"meters; X east, Y north, Z up","obj":"centimeters; X east, Y north, Z up",
                             "glb":"glTF 2.0 meters; right handed Y up; source (x,y,z) becomes (x,z,-y)",
                             "placement":"Unreal centimeters; X east, Y north, Z up; rotation_deg is [pitch,yaw,roll]",
                             "origin":"Outer Market floor center; every floor top is at world Z=0"},
              "import":{"preferred_scene_assembly":"Import separate module meshes, then instantiate placements; preview GLB is not a shipping monolithic world.",
                        "obj_import_scale":1,"glb_import_note":"glTF importer should convert meters to centimeters; calibration floor must measure 400cm.",
                        "collision":"Use per-component convex hulls in modules[].collision.hulls. A single hull over arches/canopies blocks access.",
                        "collision_geometry_units":"vertices_cm are local Unreal centimeters; vertices_m are local source meters.",
                        "navigation":"Floors/ramps: affect navigation. Objective/cover hulls: obstacles. Decorative axis marker: no collision/navigation.",
                        "lightmaps":"UV0 is planar tiling; UV1 is not authored. Generate lightmap UVs in editor if the chosen lighting workflow requires them."},
              "modules":[m.metadata() for m in modules],"rooms":ROOMS,"placements":placements,"markers":markers,"walkable_paths":paths,
              "landscape":landscape,"files":files,
              "budget":{"unique_meshes":len(modules),"static_mesh_instances":len(placements),
                        "unique_triangles":sum(sum(len(v)//3 for v in m.material_indices.values()) for m in modules),
                        "scene_triangles":sum(next(m for m in modules if m.name==p["mesh"]).metadata()["triangles"] for p in placements)},
              "limitations":["No UEFN project, .umap, .uasset, actors, devices, navmesh, HLOD, or editor-tested memory report is generated.",
                              "Static boss/objective props are geometry placeholders; bind Verse/device gameplay separately.",
                              "The kit is a flat navigable blockout, with original gothic silhouettes; finished art, texture/lightmap unwraps, lighting and audio remain editor work.",
                              "The generated collision hull recipe is validated geometrically; UEFN collision/navmesh behavior still requires Launch Session checks."]}
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=DEFAULT_OUTPUT)
    args=parser.parse_args()
    manifest=generate(args.output.resolve())
    print("AEONFALL original Ossuary starter assets generated")
    print(json.dumps(manifest["budget"],indent=2))
    print(f"Output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
