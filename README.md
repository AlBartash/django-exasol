# django-exasol

This project contains the necessary dialect to integrate EXASOL into the Django framework.

###### Please note that this is an open source project which is *not officially supported* by EXASOL. We will try to help you as much as possible, but can't guarantee anything since this is not an official EXASOL product.

# Overview of the installation procedure
Create a virtual env for this test project. Install:
Django==1.9.2
django_exabackend
pyodbc==3.0.10

1. create a new Django project (using pycharm)
2. configure exasol driver in settings.py
3. create an 'app' inside the project
```
    $ python manage.py startapp main    
```
navigating to http://127.0.0.1/main/ should give you an 'hi there!' message

4. manually create the following table in the testing EXAsol instance

        CREATE OR REPLACE TABLE "TEST"."PRODUCTS_PERMISSIONS"
        -- one entry for each permission_group/webshop/country
        (
               ID INTEGER IDENTITY,
               PERMISSION_GROUP VARCHAR(2000) NOT NULL, -- plain (eg 'sonae')
               WEBSHOP_ID VARCHAR(50) NOT NULL,
               COUNTRY_CODE VARCHAR(2) NOT NULL,
               ENABLED BOOLEAN NOT NULL,

               -- ensure uniqueness of permission_group/webshop/country
               PRIMARY KEY (PERMISSION_GROUP, WEBSHOP_ID, COUNTRY_CODE)
        );

and insert some test data

    DELETE FROM TEST.PRODUCTS_PERMISSIONS WHERE 1=1;
    INSERT INTO TEST.PRODUCTS_PERMISSIONS 
    (webshop_id, country_code, permission_group, enabled)
    values
    ('nike', 'us', 'pg1', TRUE),
    ('nike', 'es', 'pg1', TRUE),
    ('adidas', 'us', 'pg1', FALSE),
    ('adidas', 'ru', 'pg1', FALSE),
    ('adidas', 'pt', 'pg1', FALSE),
    ('nike', 'us', 'pg2', TRUE),
    ('nike', 'es', 'pg2', TRUE),
    ('adidas', 'us', 'pg2', FALSE),
    ('adidas', 'ru', 'pg2', FALSE),
    ('adidas', 'pt', 'pg2', FALSE);

5. create a model 'managed=False' so that Django doesn't try to mess with the table definition (main/models.py)

6. check that it is working by navigating to http://127.0.0.1/main/rows/ (main/views.py)

7. use the unit testing capabilities of django (main/test.py)
```
    $ python manage.py test    
```

# Detailled installation steps and run some tests

## Install ODBC driver
```sh
~$ wget https://www.exasol.com/support/secure/attachment/52896/EXASOL_ODBC-6.0.2.tar.gz
~$ tar -xzf EXASOL_ODBC-6.0.2.tar.gz
~$ ./EXASOL_ODBC-6.0.2/config_odbc
config_odbc 6.0.2 (rev. ubc/exasol/R6.0.Dev:7857)
Copyright (c) 2017 EXASOL AG
# Welcome to the EXASolution ODBC configuration program!
? continue [y]: y
? additional searchdirs [/usr/local]:
* search for driver manager libraries
  found: /usr/lib/x86_64-linux-gnu/libodbc.so.2.0.0 => uo2214lv2
  found: /usr/lib/x86_64-linux-gnu/libodbcinst.so.2.0.0 => uo2214lv2
* check for incomplete driver manager libraries
? search again (y/n)? [n]: n
# Give the connection string for EXASolution. Hostnames, IP addresses and
# IP ranges are all possible. The port is optional.
# Example: 10.0.0.1..5:1234
? connection []: 192.168.42.129:8563
* test network connection
  tcp-connect 192.168.42.129:8563
# To test ODBC connectivity we need a valid EXASolution user.
? user [sys]: sys
? password [exasol]:
* create ODBC ini file: /home//.odbc.ini
* create wrapper script: /home//EXASOL_ODBC-6.0.2/exaodbc_wrapper
  odbc-connect exasolution-uo2214lv2_64
* config summary
  available driver managers:
  * unixODBC 2.2.14 or later, libversion 2 (64bit)
    => DSN=exasolution-uo2214lv2_64
    connection test: ok
  the wrapper script sets up the neccessarry environment
  if an expected driver manager is missing, install missing packages
  or re-run this program with different --searchdir options
* create a support package
  please add support.tar to any EXASOL support request
# Guess the correct DSN for running applications.
# * Applications: open the select data source dialog (or something similar).
# * Scripting languages: load the appropriate ODBC module.
# * e.g. for python, do the following in another process: >>> import pyodbc
# Connecting to any data source is not necessary.
# Scan only processes with given pids (separated by spaces) or use '0'
# to scan all processes of the current user. (Scanning processes owned by
# other users require root access.)
? pids [0]:
* guess driver of running applications
  pid: 19459
  cmd: /home//test/djangoenv/bin/python2
  arch: 64
  lib: /usr/lib/x86_64-linux-gnu/libodbc.so.2.0.0
  dsn: exasolution-uo2214lv2_64
? scan again (y/n) [n]: n
# Configuration completed.
# If your application does not work with the correct DSN, your system
# may require setting additional environment variables.
# For how to do this, have a look at the wrapper script
# /home//EXASOL_ODBC-6.0.2/exaodbc_wrapper.
# In case of persisting problems, please contact support and include
# the generated support.tar file.
@:~$ vi .odbc.ini
```

## Setup your python 2.7 environment
```sh
~$ mkdir test
~$ cd test
~/test$ virtualenv djangoenv
Running virtualenv with interpreter /usr/bin/python2
New python executable in /home//test/djangoenv/bin/python2
Also creating executable in /home//test/djangoenv/bin/python
Installing setuptools, pkg_resources, pip, wheel...done.
@:~/test$ . djangoenv/bin/activate
(djangoenv) @:~/test$ pip install Django==1.9.2
Collecting Django==1.9.2
  Using cached Django-1.9.2-py2.py3-none-any.whl
Installing collected packages: Django
Successfully installed Django-1.9.2
(djangoenv) @:~/test$ pip install -e git+https://github.com/EXASOL/django-exasol#egg=django_exabackend
Obtaining django_exabackend from git+https://github.com/EXASOL/django-exasol#egg=django_exabackend
  Cloning https://github.com/EXASOL/django-exasol to ./djangoenv/src/django-exabackend
Collecting pyodbc<3.1,>=3.0.6 (from django_exabackend)
Installing collected packages: pyodbc, django-exabackend
  Running setup.py develop for django-exabackend
Successfully installed django-exabackend pyodbc-3.0.10
(djangoenv) @:~/test$ pip install pyodbc==3.0.10
Requirement already satisfied: pyodbc==3.0.10 in ./djangoenv/lib/python2.7/site-packages
(djangoenv) @:~/test$ pip install django_pyodbc
Requirement already satisfied: django_pyodbc in ./djangoenv/lib/python2.7/site-packages
Requirement already satisfied: pyodbc<4.1,>=3.0.6 in ./djangoenv/lib/python2.7/site-packages (from django_pyodbc)
```

## Checkout an existing django project and run some tests
```sh
(djangoenv) @:~/test$ git clone https://github.com/jabadia/exasol-django-test.git
Cloning into 'exasol-django-test'...
remote: Counting objects: 55, done.
remote: Total 55 (delta 0), reused 0 (delta 0), pack-reused 55
Unpacking objects: 100% (55/55), done.
Checking connectivity... done.
(djangoenv) @:~/test$ vi exasol-django-test/dbaccess/settings.py
# # delete following line:
# import secrets
#
# # change settings for exasol connection - it must correspond with your ~/.odbc.ini, e.g.:
#     # exasol connection
#     'exasol_db': {
#         'CONN_MAX_AGE': None,  # try to avoid new connections overhead. Not honored in development server
#         'ENGINE': 'django_exabackend',
#         'NAME': 'EXA_DB',
#         'DSN': 'exasolution-uo2214lv2_64',
#         'CONNECTIONLCCTYPE': 'en_US.UTF-8',
#         'INTTYPESINRESULTSIFPOSSIBLE': 'y',
#     },
(djangoenv) @:~/test$ cd exasol-django-test/
# with e.g. EXAplus, create a schema called "TEST" on the database:
# CREATE SCHEMA TEST;
(djangoenv) @:~/test/exasol-django-test$ python manage.py test
Setting up databases
Read only databases (no TEST db will be created): exasol_db
Creating test database for alias 'default'...
connecting to {u'DSN': 'exasolution-uo2214lv2_64', u'INTTYPESINRESULTSIFPOSSIBLE': u'y', u'CONNECTIONLCCTYPE': 'en_US.UTF-8'}
creating table
@@@ new_connection: {u'DSN': 'exasolution-uo2214lv2_64', u'INTTYPESINRESULTSIFPOSSIBLE': u'y', u'CONNECTIONLCCTYPE': 'en_US.UTF-8'}
inserting element ( nike us pg1 True )
inserted with id 1
inserting element ( nike es pg1 True )
inserted with id 2
inserting element ( adidas us pg1 False )
inserted with id 3
inserting element ( adidas ru pg1 False )
inserted with id 4
inserting element ( adidas pt pg1 False )
inserted with id 5
inserting element ( nike us pg2 True )
inserted with id 6
inserting element ( nike es pg2 True )
inserted with id 7
inserting element ( adidas us pg2 False )
inserted with id 8
inserting element ( adidas ru pg2 False )
inserted with id 9
inserting element ( adidas pt pg2 False )
inserted with id 10
dropping table
.connecting to {u'DSN': 'exasolution-uo2214lv2_64', u'INTTYPESINRESULTSIFPOSSIBLE': u'y', u'CONNECTIONLCCTYPE': 'en_US.UTF-8'}
creating table
dropping table
.connecting to {u'DSN': 'exasolution-uo2214lv2_64', u'INTTYPESINRESULTSIFPOSSIBLE': u'y', u'CONNECTIONLCCTYPE': 'en_US.UTF-8'}
creating table
inserting element ( nike us pg1 True )
inserted with id 1
inserting element ( nike es pg1 True )
inserted with id 2
inserting element ( adidas us pg1 False )
inserted with id 3
inserting element ( adidas ru pg1 False )
inserted with id 4
inserting element ( adidas pt pg1 False )
inserted with id 5
inserting element ( nike us pg2 True )
inserted with id 6
inserting element ( nike es pg2 True )
inserted with id 7
inserting element ( adidas us pg2 False )
inserted with id 8
inserting element ( adidas ru pg2 False )
inserted with id 9
inserting element ( adidas pt pg2 False )
inserted with id 10
dropping table
.connecting to {u'DSN': 'exasolution-uo2214lv2_64', u'INTTYPESINRESULTSIFPOSSIBLE': u'y', u'CONNECTIONLCCTYPE': 'en_US.UTF-8'}
creating table
inserting element ( nike us pg1 True )
inserted with id 1
inserting element ( nike es pg1 True )
inserted with id 2
inserting element ( adidas us pg1 False )
inserted with id 3
inserting element ( adidas ru pg1 False )
inserted with id 4
inserting element ( adidas pt pg1 False )
inserted with id 5
inserting element ( nike us pg2 True )
inserted with id 6
inserting element ( nike es pg2 True )
inserted with id 7
inserting element ( adidas us pg2 False )
inserted with id 8
inserting element ( adidas ru pg2 False )
inserted with id 9
inserting element ( adidas pt pg2 False )
inserted with id 10
inserting element ( elcorteingles es pg3 True )
inserted with id 11
dropping table
.
----------------------------------------------------------------------
Ran 4 tests in 2.100s

OK
Tearing down databases
Destroying test database for alias 'default'...
(djangoenv) osboxes@osboxes:~/test/exasol-django-test$
...
```
