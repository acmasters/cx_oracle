#------------------------------------------------------------------------------
# TransactionGuard.py
#   This script demonstrates the use of Transaction Guard to verify if a
# transaction has completed, ensuring that a duplicate transaction is not
# created or attempted if the application chooses to handle the error. This
# feature is only available in Oracle Database 12.1. It follows loosely the
# OCI sample provided by Oracle in its documentation about OCI and Transaction
# Guard.
#------------------------------------------------------------------------------

from __future__ import print_function

import cx_Oracle
import sys

# constants
SESSION_MIN = 1
SESSION_MAX = 9
SESSION_INCR = 2
USER_NAME = "cx_Oracle"
PASSWORD = "dev"
DATABASE = "t12-tg"

# for Python 2.7 we need raw_input
try:
    input = raw_input
except NameError:
    pass

# create transaction and generate a recoverable error
pool = cx_Oracle.SessionPool(USER_NAME, PASSWORD, DATABASE, SESSION_MIN,
        SESSION_MAX, SESSION_INCR)
connection = pool.acquire()
cursor = connection.cursor()
cursor.execute("""
        delete from TestExecuteMany
        where IntCol = 1""")
cursor.execute("""
        insert into TestExecuteMany
        values (1, null)""")
connection.commit()
input("Please kill %s session now. Press ENTER when complete." % USER_NAME)
try:
    connection.commit() # this should fail
    sys.exit("Session was not killed. Terminating.")
except cx_Oracle.DatabaseError as e:
    errorObj, = e.args
    if not errorObj.isrecoverable:
        sys.exit("Session is not recoverable. Terminating.")
ltxid = connection.ltxid
if not ltxid:
    sys.exit("Logical transaction not available. Terminating.")
pool.drop(connection)

# check if previous transaction completed
connection = pool.acquire()
cursor = connection.cursor()
_, committed, completed = cursor.callproc("dbms_app_cont.get_ltxid_outcome",
        (cx_Oracle.Binary(ltxid), cursor.var(bool), cursor.var(bool)))
print("Failed transaction was committed:", committed)
print("Failed call was completed:", completed)

