#!/usr/bin/env python3

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("inventory_api_surface.py")
SPEC = importlib.util.spec_from_file_location("inventory_api_surface", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class InventoryApiSurfaceTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.frontend = self.root / "booking_ticket_vue"
        self.backend = self.root / "ticket-system"
        (self.root / ".codex").mkdir()
        (self.frontend / "src/pages").mkdir(parents=True)
        (self.frontend / "src/components").mkdir(parents=True)
        (self.frontend / "src/services").mkdir(parents=True)
        (self.frontend / "src/constants").mkdir(parents=True)
        (self.backend / "module").mkdir(parents=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def write(self, path, content):
        path.write_text(content, encoding="utf-8")

    def test_follows_alias_and_relative_imports(self):
        page = self.frontend / "src/pages/ExamplePage.vue"
        child = self.frontend / "src/components/ChildPanel.vue"
        helper = self.frontend / "src/components/helper.js"
        self.write(
            page,
            "<script setup>\n"
            "import ChildPanel from '@/components/ChildPanel.vue'\n"
            "</script>\n",
        )
        self.write(
            child,
            "<script setup>\n"
            "import { loadTrips } from './helper'\n"
            "import { tripService } from '@/services/tripService'\n"
            "tripService.getAll()\n"
            "</script>\n",
        )
        self.write(helper, "export const loadTrips = () => null\n")
        self.write(
            self.frontend / "src/services/tripService.js",
            "export const tripService = { getAll() {} }\n",
        )

        evidence = MODULE.page_dependency_evidence(
            self.root, self.frontend, str(page)
        )

        self.assertTrue(
            any(row[0] == "src/components/ChildPanel.vue" for row in evidence)
        )

    def test_inventories_frontend_and_spring_routes(self):
        endpoint_file = self.frontend / "src/constants/api_endpoint.js"
        service_file = self.frontend / "src/services/tripService.js"
        controller = self.backend / "module/TripController.java"
        self.write(
            endpoint_file,
            "export const API_ENDPOINTS = {\n"
            "  TRIPS: {\n"
            "    BASE: '/trips',\n"
            "    BY_ID: (id) => `/trips/${id}`,\n"
            "  },\n"
            "}\n",
        )
        self.write(
            service_file,
            "apiClient.get(API_ENDPOINTS.TRIPS.BASE)\n"
            "apiClient.put(API_ENDPOINTS.TRIPS.BY_ID(id), payload)\n",
        )
        self.write(
            controller,
            '@RequestMapping("/api/trip")\n'
            "public class TripController {\n"
            "  @GetMapping\n"
            "  void list() {}\n"
            '  @PutMapping("/{id}")\n'
            "  void update() {}\n"
            "}\n",
        )

        constants = MODULE.frontend_constants(self.root, endpoint_file)
        services = MODULE.frontend_services(
            self.root, self.frontend / "src/services"
        )
        routes = MODULE.java_inventory(self.root, self.backend)

        self.assertEqual(
            [("TRIPS.BASE", "/trips"), ("TRIPS.BY_ID", "/trips/${id}")],
            [(name, path) for name, path, _ in constants],
        )
        self.assertEqual(
            [("GET", "API_ENDPOINTS.TRIPS.BASE"), ("PUT", "API_ENDPOINTS.TRIPS.BY_ID")],
            [(method, endpoint) for method, endpoint, _ in services],
        )
        self.assertEqual(
            [("GET", "/api/trip"), ("PUT", "/api/trip/{id}")],
            [(method, path) for method, path, _ in routes],
        )


if __name__ == "__main__":
    unittest.main()
