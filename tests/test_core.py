from __future__ import annotations

import unittest

from computer.monitors import virtual_bounds
from memory.semantic_vector.vector_store import add_document, search
from security.permission_manager import check_action, check_command
from security.safety_modes import set_safety_mode


class EveCoreTests(unittest.TestCase):
    def tearDown(self):
        set_safety_mode("safe_mode", "test cleanup")

    def test_safety_modes_gate_commands(self):
        set_safety_mode("safe_mode", "test")
        self.assertFalse(check_command("Remove-Item x").allowed)
        set_safety_mode("unrestricted_mode", "test")
        self.assertTrue(check_command("Remove-Item x").allowed)
        self.assertTrue(check_action("admin").allowed)

    def test_virtual_bounds_shape(self):
        bounds = virtual_bounds()
        self.assertIn("width", bounds)
        self.assertIn("height", bounds)

    def test_vector_search(self):
        add_document("unit-test", "A Eve controla rato teclado e browser por visao.")
        rows = search("rato teclado browser", limit=1)
        self.assertTrue(rows)


if __name__ == "__main__":
    unittest.main()
