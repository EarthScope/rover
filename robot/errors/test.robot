
*** Settings ***
Suite Setup      Initialize Run Dir    ${RUN_DIR}

Library    Process
Library    OperatingSystem
Resource    ../common.robot

*** Variables ***
${RUN_DIR}    ${CURDIR}${/}run

*** Test Cases ***

Bad Command
    ${result} =    Run Process    rover  foo    cwd=${RUN_DIR}
    Log    ${result.stdout}
    Log    ${result.stderr}
    Should Match Regexp    ${result.stderr}  Unknown command
    Should Match Regexp    ${result.stderr}  See .* for a list of commands

Missing File
    ${result} =    Run Process    rover  ingest  foo    cwd=${RUN_DIR}
    Log    ${result.stdout}
    Log    ${result.stderr}
    Should Match Regexp    ${result.stderr}  Cannot find
    Should Match Regexp    ${result.stderr}  See .* help ingest

Bad Mseedindex (or missing database)
    ${result} =    Run Process    rover  list-index  net\=*  --mseedindex-cmd  foo    cwd=${RUN_DIR}
    Log    ${result.stdout}
    Log    ${result.stderr}
    Should Match Regexp    ${result.stderr}  Cannot access
    Should Match Regexp    ${result.stderr}  See .* help list-index
