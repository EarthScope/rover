
*** Settings ***

Library    Process
Library    OperatingSystem

Suite Setup   Setup Run Directory


*** Keywords ***

Setup Run Directory
    Remove Directory    ${CURDIR}${/}run  recursive=True,
    Create Directory    ${CURDIR}${/}run


*** Test Cases ***

Bad Command
    ${result} =    Run Process    rover  -f  ../rover.config  foo    cwd=${CURDIR}${/}run
    Log    ${result.stdout}
    Log    ${result.stderr}
    Should Match Regexp    ${result.stderr}  Unknown command
    Should Match Regexp    ${result.stderr}  See .* for a list of commands

Missing File
    ${result} =    Run Process    rover  -f  ../rover.config  ingest  foo    cwd=${CURDIR}${/}run
    Log    ${result.stdout}
    Log    ${result.stderr}
    Should Match Regexp    ${result.stderr}  Cannot find
    Should Match Regexp    ${result.stderr}  See .* help ingest

Bad Mseedindex (or missing database)
    ${result} =    Run Process    rover  -f  ../rover.config  list-index  net\=*  --mseedindex-cmd  foo    cwd=${CURDIR}${/}run
    Log    ${result.stdout}
    Log    ${result.stderr}
    Should Match Regexp    ${result.stderr}  Cannot access
    Should Match Regexp    ${result.stderr}  See .* help list-index
