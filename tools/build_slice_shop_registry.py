#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "content" / "vertical_slice" / "slice_001_shop.json"
OUTPUT = ROOT / "verse" / "generated" / "slice_001_shop_bootstrap.verse"

def q(value: str) -> str:
    return json.dumps(str(value))

def string_array(values: list[str]) -> str:
    if not values:
        return "array{}"
    return "array{" + ", ".join(q(v) for v in values) + "}"

def cost_array(costs: list[dict]) -> str:
    if not costs:
        return "array{}"
    return "array{" + ", ".join(
        f'aeonfall_material_cost{{MaterialId := {q(c["material_id"])}, Amount := {int(c["amount"])}}}'
        for c in costs
    ) + "}"

def main() -> int:
    doc = json.loads(SOURCE.read_text(encoding="utf-8"))
    shop_id = doc["shop_id"]
    faction_id = doc.get("faction_id", "")

    lines = [
        "using { /Fortnite.com/Devices }",
        "using { /Verse.org/Simulation }",
        "",
        "# GENERATED FILE — do not hand edit.",
        "# Source: content/vertical_slice/slice_001_shop.json",
        "",
        "Slice001ShopOffers:[]aeonfall_shop_offer = array{",
    ]

    for offer in doc["offers"]:
        lines.extend([
            "    aeonfall_shop_offer{",
            f"        ShopId := {q(shop_id)},",
            f"        OfferId := {q(offer['id'])},",
            f"        OutputEntityId := {q(offer['output_entity_id'])},",
            f"        Costs := {cost_array(offer['costs'])},",
            f"        RequiredFactionId := {q(faction_id)},",
            f"        RequiredReputation := {int(offer.get('required_reputation', 0))},",
            f"        RequiredUnlockIds := {string_array(offer.get('required_unlock_ids', []))}",
            "    },",
        ])

    lines.extend([
        "}",
        "",
        "aeonfall_slice_001_shop_bootstrap_device := class(creative_device):",
        "",
        "    OnBegin<override>()<suspends>:void=",
        "        for (Offer : Slice001ShopOffers):",
        "            Registered := AEONFALLShopRegistry.Register(Offer)",
        "            if (not Registered?):",
        "                AEONFALLRuntimeBus.Emit(",
        "                    aeonfall_runtime_event{",
        '                        EventType := "bootstrap.shop_offer_registration_failed",',
        "                        SourceId := Offer.OfferId,",
        "                        TargetId := Offer.OutputEntityId",
        "                    }",
        "                )",
        "",
    ])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"generated {OUTPUT.relative_to(ROOT)} with {len(doc['offers'])} offers")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
