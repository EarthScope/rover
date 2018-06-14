
*** Settings ***

Library    Process
Library    OperatingSystem

Suite Setup   Setup Run Directory


*** Keywords ***

Setup Run Directory
    Remove Directory    ${CURDIR}${/}run  resursive=True,
    Create Directory    ${CURDIR}${/}run


*** Test Cases ***

Bad Command
    ${result} =    Run Process    rover  -f  ../roverrc  foo    cwd=${CURDIR}${/}run
    Log    ${result.stdout}
    Log    ${result.stderr}
    Should Match Regexp    ${result.stderr}  Unknown command
    Should Match Regexp    ${result.stderr}  See .* for a list of commands

Missing File
    ${result} =    Run Process    rover  -f  ../roverrc  ingest  foo    cwd=${CURDIR}${/}run
    Log    ${result.stdout}
    Log    ${result.stderr}
    Should Match Regexp    ${result.stderr}  Cannot find
    Should Match Regexp    ${result.stderr}  See .* help ingest

Bad Mseedindex (or missing database)
    ${result} =    Run Process    rover  -f  ../roverrc  list-index  net\=*  --mseedindex-cmd  foo    cwd=${CURDIR}${/}run
    Log    ${result.stdout}
    Log    ${result.stderr}
    Should Match Regexp    ${result.stderr}  Cannot access
    Should Match Regexp    ${result.stderr}  See .* help list-index

Conflicting subscriptions
    Run Process    rover  -f  ../roverrc  subscribe  IU_ANMO_00_BH1  2017-01-01  2017-01-04    cwd=${CURDIR}${/}run
    ${result} =    Run Process    rover  -f  ../roverrc  subscribe  IU_ANMO_00_BH1  2017-01-01  2017-01-04    cwd=${CURDIR}${/}run
    Log    ${result.stdout}
    Log    ${result.stderr}
    Should Match Regexp    ${result.stderr}  Overlap
    Should Match Regexp    ${result.stderr}  See .* help subscribe
