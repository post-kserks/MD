import shutil
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from db import Database, DatabaseError
from io_ops import export_table, import_table
from queries import catalog, param_names
from services import Accounting, ValidationError

TODAY = date.today().isoformat()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        path = Path(self.tmp.name) / "computers.db"
        shutil.copy2(ROOT / "data" / "computers.db", path)
        self.db = Database()
        self.db.open(path)
        self.acc = Accounting(self.db)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def status(self, inv):
        return self.db.value("SELECT status FROM computers WHERE inv_number = ?", (inv,))

    def room_id(self, building, number):
        return self.db.value("SELECT id_room FROM rooms JOIN buildings USING (id_building) "
                             "WHERE buildings.name = ? AND number = ?", (building, number))

    def expect_errors(self, fn, data, *fields):
        with self.assertRaises(ValidationError) as ctx:
            fn(data)
        for f in fields:
            self.assertIn(f, ctx.exception.errors)
        return ctx.exception.errors


class DatabaseTests(Base):
    def test_missing_file(self):
        with self.assertRaises(DatabaseError):
            Database().open(Path(self.tmp.name) / "nope.db")

    def test_not_a_database(self):
        bad = Path(self.tmp.name) / "bad.db"
        bad.write_text("это не база данных")
        with self.assertRaises(DatabaseError):
            Database().open(bad)

    def test_select_and_error(self):
        res = self.db.run("SELECT inv_number FROM computers ORDER BY 1 LIMIT 3")
        self.assertEqual(res.columns, ["inv_number"])
        self.assertEqual(len(res.rows), 3)
        with self.assertRaises(DatabaseError) as ctx:
            self.db.run("SELECT nope FROM computers")
        self.assertIn("no such column", str(ctx.exception))

    def test_dml_and_script(self):
        res = self.db.run("UPDATE computers SET hostname = hostname WHERE status = 'в резерве'")
        self.assertEqual(res.rowcount, 4)
        res = self.db.run("CREATE TEMP TABLE t (x); INSERT INTO t VALUES (1);")
        self.assertTrue(res.script)

    def test_constraint_violation_rolls_back(self):
        with self.assertRaises(DatabaseError):
            self.db.run("UPDATE computers SET status = 'сломан' WHERE inv_number = 'ПК-00002'")
        self.assertEqual(self.status("ПК-00002"), "в эксплуатации")

    def test_dependents_and_delete_restrict(self):
        deps = dict((t, n) for t, n, _ in self.db.dependents("computers", {"inv_number": "ПК-00012"}))
        self.assertEqual(deps["software_installs"], 6)
        with self.assertRaises(DatabaseError):
            self.db.delete("departments", {"id_department": 1})


class ServiceTests(Base):
    def test_register_ok(self):
        msg = self.acc.register_computer({"inv_number": "ПК-00031", "serial_number": "NEW-1", "id_model": 1,
                                          "id_room": self.room_id("Корпус Б", "Б-01"),
                                          "commission_date": TODAY, "hostname": "BUH-05"})
        self.assertIn("ПК-00031", msg)
        self.assertEqual(self.status("ПК-00031"), "в резерве")

    def test_register_validation(self):
        serial = self.db.value("SELECT serial_number FROM computers WHERE inv_number = 'ПК-00002'")
        errors = self.expect_errors(self.acc.register_computer, {
            "inv_number": "PC-1", "serial_number": serial, "id_model": 1,
            "id_room": self.room_id("Главный корпус", "101"), "commission_date": "31.12.2026",
            "hostname": "плохое имя"}, "inv_number", "serial_number", "id_room", "commission_date", "hostname")
        self.assertIn("ПК-NNNNN", errors["inv_number"])

    def test_assign_and_return(self):
        self.acc.assign_computer({"inv_number": "ПК-00004", "tab_number": "100102", "issue_date": TODAY,
                                  "id_room": self.room_id("Главный корпус", "101")})
        self.assertEqual(self.status("ПК-00004"), "в эксплуатации")
        aid = self.db.value("SELECT id_assignment FROM assignments WHERE inv_number = 'ПК-00004' "
                            "AND return_date IS NULL")
        self.acc.return_computer({"id_assignment": aid, "return_date": TODAY,
                                  "id_room": self.room_id("Главный корпус", "001")})
        self.assertEqual(self.status("ПК-00004"), "в резерве")

    def test_assign_business_rules(self):
        self.expect_errors(self.acc.assign_computer, {
            "inv_number": "ПК-00002", "tab_number": "100103", "issue_date": "2000-01-01",
            "id_room": self.room_id("Главный корпус", "001")}, "inv_number", "tab_number", "issue_date", "id_room")

    def test_service_cycle(self):
        self.acc.open_service({"inv_number": "ПК-00002", "work_type": "ремонт", "start_date": TODAY,
                               "executor_tab_number": "400402"})
        self.assertEqual(self.status("ПК-00002"), "в ремонте")
        sid = self.db.value("SELECT id_service FROM services WHERE inv_number = 'ПК-00002' AND end_date IS NULL")
        self.acc.close_service({"id_service": sid, "end_date": TODAY, "works_done": "Замена вентилятора",
                                "cost": "1500,50"})
        self.assertEqual(self.status("ПК-00002"), "в эксплуатации")
        self.assertEqual(self.db.value("SELECT cost FROM services WHERE id_service = ?", (sid,)), 1500.5)

    def test_service_rules(self):
        self.expect_errors(self.acc.open_service, {
            "inv_number": "ПК-00006", "work_type": "ремонт", "start_date": TODAY,
            "executor_tab_number": "400402", "service_org": "ООО «СервисПлюс»"}, "inv_number", "executor_tab_number")
        sid = self.db.value("SELECT id_service FROM services WHERE inv_number = 'ПК-00006' AND end_date IS NULL")
        self.expect_errors(self.acc.close_service, {"id_service": sid, "end_date": "2000-01-01", "cost": "-5"},
                           "end_date", "works_done", "cost")

    def test_server_returns_to_operation(self):
        sid = self.db.value("SELECT id_service FROM services WHERE inv_number = 'ПК-00019' AND end_date IS NULL")
        self.acc.close_service({"id_service": sid, "end_date": TODAY, "works_done": "Замена контроллера"})
        self.assertEqual(self.status("ПК-00019"), "в эксплуатации")

    def test_write_off(self):
        self.acc.write_off({"inv_number": "ПК-00005", "writeoff_date": TODAY, "components_to_stock": "1"})
        self.assertEqual(self.status("ПК-00005"), "списан")
        self.assertEqual(self.db.value("SELECT COUNT(*) FROM assignments WHERE inv_number = 'ПК-00005' "
                                       "AND return_date IS NULL"), 0)
        self.assertEqual(self.db.value("SELECT COUNT(*) FROM components WHERE inv_number = 'ПК-00005'"), 0)
        self.expect_errors(self.acc.write_off, {"inv_number": "ПК-00006", "writeoff_date": TODAY}, "inv_number")

    def test_license_limit(self):
        photoshop = self.db.value("SELECT id_program FROM programs WHERE name = 'Adobe Photoshop'")
        errors = self.expect_errors(self.acc.install_program, {"inv_number": "ПК-00012", "id_program": photoshop,
                                                               "install_date": TODAY}, "id_program")
        self.assertIn("2 из 2", errors["id_program"])
        zip7 = self.db.value("SELECT id_program FROM programs WHERE name = '7-Zip'")
        self.acc.install_program({"inv_number": "ПК-00011", "id_program": zip7, "install_date": TODAY})

    def test_lookups(self):
        self.assertEqual(sum(self.acc.stats().values()), 30)
        self.assertTrue(all("в резерве" in label for _, label in self.acc.reserve_computers()))
        self.assertFalse(any("Сидоров" in label for _, label in self.acc.employees()))


class IoAndQueryTests(Base):
    def test_export_import_roundtrip(self):
        for fmt in ("csv", "json"):
            path = Path(self.tmp.name) / f"programs.{fmt}"
            n = export_table(self.db, "programs", path, fmt)
            self.assertEqual(n, self.db.value("SELECT COUNT(*) FROM programs"))
            total, added = import_table(self.db, "programs", path, fmt, skip_existing=True)
            self.assertEqual((total, added), (n, 0))
            with self.assertRaises(DatabaseError):
                import_table(self.db, "programs", path, fmt)

    def test_import_unknown_column(self):
        path = Path(self.tmp.name) / "bad.csv"
        path.write_text("name,nope\nX,1\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            import_table(self.db, "programs", path, "csv")

    def test_catalog_runs(self):
        items = catalog()
        self.assertGreaterEqual(len(items), 18)
        for title, sql, params in items:
            values = {k: default for k, (_, default) in params.items()}
            self.assertEqual(set(param_names(sql)), set(values), title)
            res = self.db.run(sql, values)
            self.assertTrue(res.is_select, title)
        var18 = next(sql for title, sql, _ in items if "больше N" in title)
        self.assertEqual(len(self.db.run(var18, {"n": 5}).rows), 2)
        self.assertEqual(len(self.db.run(var18, {"n": 2}).rows), 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
