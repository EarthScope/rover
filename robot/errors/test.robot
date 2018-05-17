
*** Settings ***

Library    Process
Library    OperatingSystem

Test Setup    Set Environment Variable    PYTHONPATH  ../../../../rover
Suite Setup   Setup Run Directory


*** Keywords ***

Setup Run Directory
    Remove Directory    ${CURDIR}${/}run  resursive=True,
    Create Directory    ${CURDIR}${/}run


*** Test Cases ***

Bad Command
    ${result} =    Run Process    python  -m  rover  -f  ../roverrc  foo    cwd=${CURDIR}${/}run
    Log    ${result.stdout}
    Log    ${result.stderr}
    Should Match Regexp    ${result.stderr}  Unknown command
    Should Match Regexp    ${result.stderr}  See .* for a list of commands

Missing File
    ${result} =    Run Process    python  -m  rover  -f  ../roverrc  ingest  foo    cwd=${CURDIR}${/}run
    Log    ${result.stdout}
    Log    ${result.stderr}
    Should Match Regexp    ${result.stderr}  Cannot find
    Should Match Regexp    ${result.stderr}  See .* help ingest

Bad Mseedindex
    ${result} =    Run Process    python  -m  rover  -f  ../roverrc  list-index  net\=*  --mseed-cmd  foo    cwd=${CURDIR}${/}run
    Log    ${result.stdout}
    Log    ${result.stderr}
    Should Match Regexp    ${result.stderr}  Cannot access
    Should Match Regexp    ${result.stderr}  See .* help list-index
