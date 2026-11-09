import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "db" / "computers.db"

RULES = [
    ("БО1", "не более одного действующего закрепления у компьютера", """
        SELECT inv_number FROM assignments WHERE return_date IS NULL
        GROUP BY inv_number HAVING COUNT(*) > 1"""),
    ("БО2", "действующие закрепления только за неуволенными сотрудниками", """
        SELECT a.id_assignment FROM assignments a JOIN employees e USING (tab_number)
        WHERE a.return_date IS NULL AND e.dismissal_date IS NOT NULL"""),
    ("БО3", "«в резерве» — без закрепления и на складе", """
        SELECT c.inv_number FROM computers c JOIN rooms r USING (id_room)
        WHERE c.status = 'в резерве'
          AND (r.room_type <> 'склад' OR EXISTS (SELECT 1 FROM assignments a
               WHERE a.inv_number = c.inv_number AND a.return_date IS NULL))"""),
    ("БО3", "«в эксплуатации» — есть закрепление или стоит в серверной", """
        SELECT c.inv_number FROM computers c JOIN rooms r USING (id_room)
        WHERE c.status = 'в эксплуатации' AND r.room_type <> 'серверная'
          AND NOT EXISTS (SELECT 1 FROM assignments a
                          WHERE a.inv_number = c.inv_number AND a.return_date IS NULL)"""),
    ("БО4", "«в ремонте» ⇔ есть незавершённое обслуживание", """
        SELECT c.inv_number FROM computers c
        WHERE (c.status = 'в ремонте') <> EXISTS (SELECT 1 FROM services s
               WHERE s.inv_number = c.inv_number AND s.end_date IS NULL)"""),
    ("БО5", "у списанного нет действующего закрепления", """
        SELECT c.inv_number FROM computers c JOIN assignments a USING (inv_number)
        WHERE c.status = 'списан' AND a.return_date IS NULL"""),
    ("БО6", "закрепления уволенного завершены не позже даты увольнения", """
        SELECT a.id_assignment FROM assignments a JOIN employees e USING (tab_number)
        WHERE e.dismissal_date IS NOT NULL
          AND (a.return_date IS NULL OR a.return_date > e.dismissal_date)"""),
    ("БО8", "установок платной программы не больше, чем лицензий", """
        SELECT p.name FROM programs p JOIN software_installs i USING (id_program)
        WHERE p.license_type <> 'бесплатная'
        GROUP BY p.id_program HAVING COUNT(*) > p.license_count"""),
    ("ОЦ3", "закрепление в пределах срока эксплуатации компьютера", """
        SELECT a.id_assignment FROM assignments a JOIN computers c USING (inv_number)
        WHERE a.issue_date < c.commission_date
           OR (c.writeoff_date IS NOT NULL AND COALESCE(a.return_date, '9999') > c.writeoff_date)"""),
    ("ОЦ3", "обслуживание в пределах срока эксплуатации компьютера", """
        SELECT s.id_service FROM services s JOIN computers c USING (inv_number)
        WHERE s.start_date < c.commission_date
           OR (c.writeoff_date IS NOT NULL AND s.start_date > c.writeoff_date)"""),
    ("ОЦ5", "периоды закреплений одного компьютера не пересекаются", """
        SELECT a.id_assignment FROM assignments a JOIN assignments b
          ON a.inv_number = b.inv_number AND a.id_assignment < b.id_assignment
        WHERE a.issue_date <= COALESCE(b.return_date, '9999')
          AND b.issue_date <= COALESCE(a.return_date, '9999')"""),
]


def validate(db_path=DB):
    con = sqlite3.connect(db_path)
    failed = 0
    for code, title, sql in RULES:
        bad = [r[0] for r in con.execute(sql)]
        failed += bool(bad)
        mark = "ok" if not bad else "НАРУШЕНО: " + ", ".join(map(str, bad[:5]))
        print(f"{code:4} {title:62} {mark}")
    con.close()
    return failed


if __name__ == "__main__":
    sys.exit(1 if validate() else 0)
