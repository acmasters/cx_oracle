"""Module for testing features introduced in 12.1"""

import sys

if sys.version_info > (3,):
    long = int

class TestFeatures12_1(BaseTestCase):

    def testArrayDMLRowCountsOff(self):
        "test executing with arraydmlrowcounts mode disabled"
        self.cursor.execute("truncate table TestArrayDML")
        rows = [ (1, "First"),
                 (2, "Second") ]
        sql = "insert into TestArrayDML (IntCol,StringCol) values (:1,:2)"
        self.cursor.executemany(sql, rows, arraydmlrowcounts = False)
        self.assertRaises(cx_Oracle.DatabaseError,
                self.cursor.getarraydmlrowcounts)
        rows = [ (3, "Third"),
                 (4, "Fourth") ]
        self.cursor.executemany(sql, rows)
        self.assertRaises(cx_Oracle.DatabaseError,
                self.cursor.getarraydmlrowcounts)

    def testArrayDMLRowCountsOn(self):
        "test executing with arraydmlrowcounts mode enabled"
        self.cursor.execute("truncate table TestArrayDML")
        rows = [ ( 1, "First", 100),
                 ( 2, "Second", 200),
                 ( 3, "Third", 300),
                 ( 4, "Fourth", 300),
                 ( 5, "Fifth", 300) ]
        sql = "insert into TestArrayDML (IntCol,StringCol,IntCol2) " \
                "values (:1,:2,:3)"
        self.cursor.executemany(sql, rows, arraydmlrowcounts = True)
        self.connection.commit()
        self.assertEqual(self.cursor.getarraydmlrowcounts(),
                [long(1), long(1), long(1), long(1), long(1)])
        self.cursor.execute("select count(*) from TestArrayDML")
        count, = self.cursor.fetchone()
        self.assertEqual(count, len(rows))

    def testExceptionInIteration(self):
        "test executing with arraydmlrowcounts with exception"
        self.cursor.execute("truncate table TestArrayDML")
        rows = [ (1, "First"),
                 (2, "Second"),
                 (2, "Third"),
                 (4, "Fourth") ]
        sql = "insert into TestArrayDML (IntCol,StringCol) values (:1,:2)"
        self.assertRaises(cx_Oracle.DatabaseError, self.cursor.executemany,
                sql, rows, arraydmlrowcounts = True)
        self.assertEqual(self.cursor.getarraydmlrowcounts(),
                [long(1), long(1)])

    def testExecutingDelete(self):
        "test executing delete statement with arraydmlrowcount mode"
        self.cursor.execute("truncate table TestArrayDML")
        rows = [ (1, "First", 100),
                 (2, "Second", 200),
                 (3, "Third", 300),
                 (4, "Fourth", 300),
                 (5, "Fifth", 300),
                 (6, "Sixth", 400),
                 (7, "Seventh", 400),
                 (8, "Eighth", 500) ]
        sql = "insert into TestArrayDML (IntCol,StringCol,IntCol2) " \
                "values (:1, :2, :3)"
        self.cursor.executemany(sql, rows)
        rows = [ (200,), (300,), (400,) ]
        statement = "delete from TestArrayDML where IntCol2 = :1"
        self.cursor.executemany(statement, rows, arraydmlrowcounts = True)
        self.assertEqual(self.cursor.getarraydmlrowcounts(),
                [long(1), long(3), long(2)])

    def testExecutingUpdate(self):
        "test executing update statement with arraydmlrowcount mode"
        self.cursor.execute("truncate table TestArrayDML")
        rows = [ (1, "First",100),
                 (2, "Second",200),
                 (3, "Third",300),
                 (4, "Fourth",300),
                 (5, "Fifth",300),
                 (6, "Sixth",400),
                 (7, "Seventh",400),
                 (8, "Eighth",500) ]
        sql = "insert into TestArrayDML (IntCol,StringCol,IntCol2) " \
                "values (:1, :2, :3)"
        self.cursor.executemany(sql, rows)
        rows = [ ("One", 100),
                 ("Two", 200),
                 ("Three", 300),
                 ("Four", 400) ]
        sql = "update TestArrayDML set StringCol = :1 where IntCol2 = :2"
        self.cursor.executemany(sql, rows, arraydmlrowcounts = True)
        self.assertEqual(self.cursor.getarraydmlrowcounts(),
                [long(1), long(1), long(3), long(2)])

    def testImplicitResults(self):
        "test getimplicitresults() returns the correct data"
        self.cursor.execute("""
                declare
                    c1 sys_refcursor;
                    c2 sys_refcursor;
                begin

                    open c1 for
                    select NumberCol
                    from TestNumbers
                    where IntCol between 3 and 5;

                    dbms_sql.return_result(c1);

                    open c2 for
                    select NumberCol
                    from TestNumbers
                    where IntCol between 7 and 10;

                    dbms_sql.return_result(c2);

                end;""")
        results = self.cursor.getimplicitresults()
        self.assertEqual(len(results), 2)
        self.assertEqual([n for n, in results[0]], [3.75, 5, 6.25])
        self.assertEqual([n for n, in results[1]], [8.75, 10, 11.25, 12.5])

    def testImplicitResultsNoStatement(self):
        "test getimplicitresults() without executing a statement"
        self.assertRaises(cx_Oracle.InterfaceError,
                self.cursor.getimplicitresults)

    def testInsertWithBatchError(self):
        "test executing insert with multiple distinct batch errors"
        self.cursor.execute("truncate table TestArrayDML")
        rows = [ (1, "First", 100),
                 (2, "Second", 200),
                 (2, "Third", 300),
                 (4, "Fourth", 400),
                 (5, "Fourth", 1000)]
        sql = "insert into TestArrayDML (IntCol, StringCol, IntCol2) " \
                "values (:1, :2, :3)"
        self.cursor.executemany(sql, rows, batcherrors = True,
                arraydmlrowcounts = True)
        expectedErrors = [
                ( 4, 1438, "ORA-01438: value larger than specified " \
                        "precision allowed for this column\n" ),
                ( 2, 1, "ORA-00001: unique constraint " \
                        "(CX_ORACLE.TESTARRAYDML_PK) violated\n")
        ]
        actualErrors = [(e.offset, e.code, e.message) \
                for e in self.cursor.getbatcherrors()]
        self.assertEqual(actualErrors, expectedErrors)
        self.assertEqual(self.cursor.getarraydmlrowcounts(),
                [long(1), long(1), long(0), long(1), long(0)])

    def testBatchErrorFalse(self):
        "test batcherrors mode set to False"
        self.cursor.execute("truncate table TestArrayDML")
        rows = [ (1, "First", 100),
                 (2, "Second", 200),
                 (2, "Third", 300) ]
        sql = "insert into TestArrayDML (IntCol, StringCol, IntCol2) " \
                "values (:1, :2, :3)"
        self.assertRaises(cx_Oracle.IntegrityError,
                self.cursor.executemany, sql, rows, batcherrors = False)

    def testUpdatewithBatchError(self):
        "test executing in succession with batch error"
        self.cursor.execute("truncate table TestArrayDML")
        rows = [ (1, "First", 100),
                 (2, "Second", 200),
                 (3, "Third", 300),
                 (4, "Second", 300),
                 (5, "Fifth", 300),
                 (6, "Sixth", 400),
                 (6, "Seventh", 400),
                 (8, "Eighth", 100) ]
        sql = "insert into TestArrayDML (IntCol, StringCol, IntCol2) " \
                "values (:1, :2, :3)"
        self.cursor.executemany(sql, rows, batcherrors = True)
        expectedErrors = [
                ( 6, 1, "ORA-00001: unique constraint " \
                        "(CX_ORACLE.TESTARRAYDML_PK) violated\n")
        ]
        actualErrors = [(e.offset, e.code, e.message) \
                for e in self.cursor.getbatcherrors()]
        self.assertEqual(actualErrors, expectedErrors)
        rows = [ (101, "First"),
                 (201, "Second"),
                 (3000, "Third"),
                 (900, "Ninth"),
                 (301, "Third") ]
        sql = "update TestArrayDML set IntCol2 = :1 where StringCol = :2"
        self.cursor.executemany(sql, rows, arraydmlrowcounts = True,
                batcherrors = True)
        expectedErrors = [
                ( 2, 1438, "ORA-01438: value larger than specified " \
                        "precision allowed for this column\n" )
        ]
        actualErrors = [(e.offset, e.code, e.message) \
                for e in self.cursor.getbatcherrors()]
        self.assertEqual(actualErrors, expectedErrors)
        self.assertEqual(self.cursor.getarraydmlrowcounts(),
                [long(1), long(2), long(0), long(0), long(1)])
        self.assertEqual(self.cursor.rowcount, 4)

