
*** Settings ***

Library    Process
Library    OperatingSystem

Suite Setup   Setup Run Directory


*** Keywords ***

Setup Run Directory
    Remove Directory    ${CURDIR}${/}run  resursive=True,
    Create Directory    ${CURDIR}${/}run


*** Test Cases ***

Help
    Comment  check that help starts and shows basic info
    ${result} =    Run Process    rover  -f  ../roverrc  cwd=${CURDIR}${/}run
    Log    ${result.stdout}
    Log    ${result.stderr}
    Should Match Regexp    ${result.stdout}  help
    Should Match Regexp    ${result.stdout}  roverrc
