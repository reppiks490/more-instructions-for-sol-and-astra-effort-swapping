#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "content" / "world" / "world_topology.json"
OUTPUT = ROOT / "verse" / "generated" / "world_topology_bootstrap.verse"

BAND_MAP = {
    "low": "Low",
    "medium": "Medium",
    "high": "High",
    "cinematic": "Cinematic",
}

def q(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'

def arr(values: list[str]) -> str:
    return "array{" + ", ".join(q(v) for v in values) + "}"

def main() -> int:
    doc = json.loads(SOURCE.read_text(encoding="utf-8"))
    lines = [
        "using { /Fortnite.com/Devices }",
        "using { /Verse.org/Simulation }",
        "",
        "# GENERATED FILE — do not hand edit.",
        "# Source: content/world/world_topology.json",
        "",
        "AEONFALLWorldRegionDefinitions:[]aeonfall_region_definition = array{",
    ]

    for region in doc.get("regions", []):
        band = BAND_MAP[region.get("streaming_band", "medium")]
        lines.extend([
            "    aeonfall_region_definition{",
            f"        RegionId := {q(region['id'])},",
            f"        DisplayName := {q(region['name'])},",
            f"        NeighborRegionIds := {arr(region.get('neighbors', []))},",
            f"        StreamingBand := aeonfall_region_streaming_band.{band},",
            f"        VerticalSlice := {'true' if region.get('vertical_slice') else 'false'}",
            "    },",
        ])

    lines.extend([
        "}",
        "",
        "aeonfall_world_topology_bootstrap_device := class(creative_device):",
        "",
        "    OnBegin<override>()<suspends>:void=",
        "        for (Definition : AEONFALLWorldRegionDefinitions):",
        "            Registered := GetAEONFALLRegionRegistry().Register(Definition)",
        "            if (Registered?):",
        "                Initialized := GetAEONFALLRegionRuntime().InitializeRegion(Definition.RegionId)",
        "                if (not Initialized?):",
        "                    AEONFALLRuntimeBus.Emit(",
        "                        aeonfall_runtime_event{",
        '                            EventType := "bootstrap.region_initialization_failed",',
        "                            SourceId := Definition.RegionId",
        "                        }",
        "                    )",
        "            else:",
        "                AEONFALLRuntimeBus.Emit(",
        "                    aeonfall_runtime_event{",
        '                        EventType := "bootstrap.region_registration_failed",',
        "                        SourceId := Definition.RegionId",
        "                    }",
        "                )",
        "",
    ])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"generated {OUTPUT.relative_to(ROOT)} with {len(doc.get('regions', []))} regions")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
