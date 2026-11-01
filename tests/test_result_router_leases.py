"""Source-mutation checks for the two first-playable result routers.

These checks do not compile Verse or exercise native event subscriptions.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ROUTERS = {
    "ability": (
        "verse/combat/ability_result_router_device.verse",
        "aeonfall_ability_result_router_device",
        "aeonfall_ability_result_router_lease",
        "AEONFALLAbilityResultRouterLeaseSessions",
        "GetAEONFALLAbilityResultRouterLease",
        "AEONFALLRuntimeBus.AdapterResult.Subscribe(OnAdapterResult)",
    ),
    "unlock": (
        "verse/economy/unlock_delivery_router_device.verse",
        "aeonfall_unlock_delivery_router_device",
        "aeonfall_unlock_delivery_router_lease",
        "AEONFALLUnlockDeliveryRouterLeaseSessions",
        "GetAEONFALLUnlockDeliveryRouterLease",
        "AEONFALLRuntimeBus.UnlockDeliveryResult.Subscribe(OnResult)",
    ),
}


def check_router(source: str, spec: tuple[str, ...]) -> list[str]:
    _, device, lease, sessions, getter, subscribe = spec
    code = "\n".join(line.split("#", 1)[0] for line in source.splitlines())
    errors: list[str] = []
    begin = code.partition("    OnBegin<override>()<suspends>:void=")[2].partition(
        "    OnEnd<override>():void="
    )[0]
    end = code.partition("    OnEnd<override>():void=")[2].partition(
        "    OnResult("
    )[0].partition("    OnAdapterResult(")[0]
    acquire = begin.find(f"Acquired := {getter}().Acquire(Self)")
    reject = begin.find("if (not Acquired?):")
    abort = begin.find("return", reject)
    owned = begin.find("set LeaseOwned = true")
    listener = begin.find(subscribe)
    if min(acquire, reject, abort, owned, listener) < 0 or not (
        acquire < reject < abort < owned < listener
    ):
        errors.append("duplicate router must be rejected before subscription")

    guard = end.find("if (LeaseOwned?):")
    disown = end.find("set LeaseOwned = false")
    cancel = end.find("Subscription.Cancel()")
    release = end.find(f"{getter}().Release(Self)")
    if min(guard, disown, cancel, release) < 0 or not (
        guard < disown < cancel < release
    ):
        errors.append("only owning router may cancel and release after subscription")

    for token in (
        f"{lease} := class():",
        f"var Owner:?{device} = false",
        f"Acquire(Device:{device})<transacts>:logic=",
        "if (Owner?):",
        "set Owner = option{Device}",
        f"Release(Device:{device})<transacts>:logic=",
        "if (Current := Owner?, Current = Device):",
        "set Owner = false",
        f"var {sessions}:weak_map(session, {lease}) = map{{}}",
        f"{getter}()<transacts>:{lease}=",
        f"Existing := {sessions}[CurrentSession]",
        f"set {sessions}[CurrentSession] = Created",
        "Err(",
    ):
        if token not in code:
            errors.append(f"missing exclusive session lease: {token}")
    return errors


class ResultRouterLeaseSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {
            name: (ROOT / spec[0]).read_text(encoding="utf-8")
            for name, spec in ROUTERS.items()
        }

    def test_both_routers_are_guarded(self):
        for name, spec in ROUTERS.items():
            with self.subTest(router=name):
                self.assertEqual(check_router(self.sources[name], spec), [])

    def assert_mutation_rejected(self, name: str, old: str, new: str):
        source = self.sources[name]
        self.assertIn(old, source)
        changed = source.replace(old, new, 1)
        self.assertNotEqual(source, changed)
        self.assertTrue(check_router(changed, ROUTERS[name]))

    def test_reject_removed_acquisition(self):
        for name, spec in ROUTERS.items():
            with self.subTest(router=name):
                self.assert_mutation_rejected(
                    name, f"Acquired := {spec[4]}().Acquire(Self)",
                    "Acquired := true"
                )

    def test_reject_unguarded_subscription(self):
        for name in ROUTERS:
            with self.subTest(router=name):
                self.assert_mutation_rejected(
                    name, "if (not Acquired?):", "if (Acquired?):"
                )

    def test_reject_subscribing_before_lease(self):
        for name, spec in ROUTERS.items():
            with self.subTest(router=name):
                self.assert_mutation_rejected(
                    name,
                    f"        set LeaseOwned = true\\n        Subscription := {spec[5]}",
                    f"        Subscription := {spec[5]}\\n        set LeaseOwned = true"
                )

    def test_reject_unowned_teardown(self):
        for name in ROUTERS:
            with self.subTest(router=name):
                self.assert_mutation_rejected(
                    name, "if (LeaseOwned?):", "if (not LeaseOwned?):"
                )

    def test_reject_cross_owner_release(self):
        for name in ROUTERS:
            with self.subTest(router=name):
                self.assert_mutation_rejected(
                    name, "if (Current := Owner?, Current = Device):",
                    "if (Current := Owner?):"
                )

    def test_reject_missing_cancel(self):
        for name in ROUTERS:
            with self.subTest(router=name):
                self.assert_mutation_rejected(
                    name, "Subscription.Cancel()", "Subscription = Subscription"
                )

    def test_reject_missing_release(self):
        for name, spec in ROUTERS.items():
            with self.subTest(router=name):
                self.assert_mutation_rejected(
                    name, f"{spec[4]}().Release(Self)", "true"
                )


if __name__ == "__main__":
    unittest.main()
